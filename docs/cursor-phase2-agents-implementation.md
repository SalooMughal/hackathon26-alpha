# Cursor System Prompt — AI Standup Bot (Phase 2: Implement the Agentic Pipeline)

You are a senior AI engineer. Phase 1 (scaffold, DB, endpoints, seeder, stubbed graph) is already complete and working. Your job now is to implement the REAL multi-agent LangGraph pipeline end to end, in one pass, following this spec exactly. Do not restructure the existing project; only fill in and extend it.

## Context you must respect

- Existing structure: `app/agents/{state.py, graph.py, llm.py, nodes/, prompts/}`, `app/schemas/`, `app/services/summary_service.py` — as scaffolded in Phase 1.
- Prompt files already exist in the project `docs/` folder: `sanitizer_v1.txt`, `planner_v1.txt`, `summarizer_v1.txt`, `validator_v1.txt`. FIRST ACTION: copy them into `app/agents/prompts/` (that directory is the runtime source; docs keeps the reference copies).
- LLM provider: OpenAI via `langchain-openai` (`ChatOpenAI`). Models/temperatures come from settings, never hardcoded.
- All state, agent I/O structures, and settings use Pydantic v2 models.
- Pipeline: sanitizer → planner → summarizer → parser → (conditional) → validator → (conditional) → END, with bounded revision loops back to summarizer and a deterministic fallback path.

## Step 0 — Dependencies & config

1. Ensure installed and pinned: `langgraph`, `langchain-core`, `langchain-openai`.
2. Extend `core/config.py` (pydantic-settings) with: `SANITIZER_MODEL=gpt-4o-mini`, `PLANNER_MODEL=gpt-4o-mini`, `SUMMARIZER_MODEL=gpt-4o`, `VALIDATOR_MODEL=gpt-4o-mini`, `LLM_TIMEOUT_SECONDS=30`, `LLM_MAX_RETRIES=2`, `MAX_REVISIONS=2`, `GRAPH_RECURSION_LIMIT=15`. Update `.env.example` to match.

## Step 1 — Pydantic schemas (`app/schemas/`)

Create/complete these models (Pydantic v2, full type hints, docstrings):

`schemas/sanitized.py`
- `MemberFlag(str, Enum)`: sexual_content, harassment_or_abuse, hate_speech, violence_threat, profanity, prompt_injection, credentials_or_pii, spam_or_off_topic
- `SanitizedMember`: name: str, yesterday: str, today: str, blockers: str, was_modified: bool, flags: list[MemberFlag] = [], fully_redacted: bool = False
- `SanitizedUpdates`: members: list[SanitizedMember], notes: list[str] = []

`schemas/plan.py`
- `SummaryPlan`: grouping: Literal["by_section","by_person"], section_order: list[str], emphasis: list[str], cross_link_hints: list[str] = [], tone: Literal["neutral","urgent"], length_budget_words: int (ge=80, le=220)

`schemas/summary.py`
- `PersonItems`: person: str, items: list[str]
- `Blocker`: person: str, item: str, severity: Literal["low","medium","high"]
- `StandupSummary`: tldr: str, done: list[PersonItems], doing: list[PersonItems], blockers: list[Blocker], cross_links: list[str] = []
- Pure function `render_markdown(summary: StandupSummary, standup_date: date, degraded: bool = False) -> str` producing Slack-flavored markdown (*Done* / *Doing* / *Blockers* sections, TL;DR on top, a "⚠ auto-generated without AI validation" footer line only when degraded). Deterministic, no LLM, unit-testable.

`schemas/validation.py`
- `ValidationResult`: approved: bool, issues: list[str] = [] (validator: max 5 issues)

## Step 2 — Graph state (`app/agents/state.py`)

Replace the stub state with a Pydantic model used directly as the LangGraph state schema:

```python
class GraphState(BaseModel):
    standup_date: str
    raw_updates: list[dict]                     # input from service, untouched
    sanitized_updates: SanitizedUpdates | None = None
    plan: SummaryPlan | None = None
    raw_summary_output: str | None = None       # summarizer's raw string
    parsed_summary: StandupSummary | None = None
    validation: ValidationResult | None = None
    feedback: str | None = None                 # routed back to summarizer
    revision_count: int = 0
    status: Literal["in_progress","validated","degraded"] = "in_progress"
    error: str | None = None
    usage: dict = {}                            # per-node token usage accumulation
```

Nodes return PARTIAL updates as plain dicts containing only changed fields; LangGraph merges/validates against this model.

## Step 3 — Prompt loader (`app/agents/prompts/loader.py`)

The prompt .txt files contain a commented header, then `## SYSTEM MESSAGE`, then `## HUMAN MESSAGE TEMPLATE` (summarizer also has `## FEEDBACK BLOCK TEMPLATE`). Implement:

```python
class PromptParts(BaseModel):
    system: str
    human_template: str
    feedback_template: str | None = None

@lru_cache
def load_prompt(name: str) -> PromptParts: ...
```

Rules:
- Split the file on the `## ` section headers; drop lines starting with `#` before the first section header (the wiring comments).
- CRITICAL: system messages are used VERBATIM as the system message string. NEVER call `.format()` on them and never pass them through f-string ChatPromptTemplate — the summarizer system message contains literal JSON braces and will break. Only `human_template` (and `feedback_template`) are formatted with `str.format(**kwargs)`; they contain no literal braces by design.
- Build messages manually as `[SystemMessage(content=parts.system), HumanMessage(content=parts.human_template.format(...))]`. Do not use ChatPromptTemplate anywhere.

Also implement `format_team_updates(members: list[SanitizedMember] | list[dict]) -> str` producing, per member:
```
<member name="{name}">
yesterday: {text}
today: {text}
blockers: {text or "none stated"}
</member>
```

## Step 4 — LLM factory (`app/agents/llm.py`)

```python
Role = Literal["sanitizer","planner","summarizer","validator"]
def get_llm(role: Role) -> ChatOpenAI: ...
```
- Reads model name from settings per role; temperature: summarizer 0.2, all others 0; `timeout=settings.LLM_TIMEOUT_SECONDS`, `max_retries=settings.LLM_MAX_RETRIES`.
- No module-level clients; the factory builds on demand (cache with lru_cache keyed by role is fine).
- Structured-output roles bind here: provide `get_structured_llm(role, schema)` returning `get_llm(role).with_structured_output(schema)`.

## Step 5 — Nodes (`app/agents/nodes/`)

General rules for every node:
- Signature: `async def node_name(state: GraphState) -> dict`.
- Wrap the LLM call in try/except. On exception: log with structlog (node, error, request context) and return `{"status": "degraded", "error": f"{node_name}: {exc}"}` — EXCEPT the sanitizer, which fails open (see below). Routing sends degraded status to the fallback node.
- Log per node: node name, duration_ms, revision_count.
- Accumulate token usage: read `usage_metadata` from the AI message when available (for structured output, call with `include_raw=True` and read `result["raw"].usage_metadata`, parsed object is `result["parsed"]`); merge into `state.usage` under the node's key `{input_tokens, output_tokens}`. If unavailable, store zeros — never fail on missing usage.

`sanitizer.py`
- Deterministic pre-clean in code FIRST (also used on raw input in the service): strip control chars, collapse whitespace, hard-cap each field at 2000 chars, empty → "".
- LLM call: system = sanitizer_v1 verbatim; human = template formatted with standup_date and `format_team_updates(raw_updates)`. Structured output → `SanitizedUpdates`.
- Post-check in code: every input member name must exist in the output exactly once; if the model dropped or renamed anyone, restore that member's pre-cleaned raw fields with `was_modified=False`.
- FAIL OPEN: if the LLM call fails entirely, build `SanitizedUpdates` from the pre-cleaned raw input (all flags empty), log a warning, continue the pipeline. The sanitizer must never kill a standup.
- Returns `{"sanitized_updates": ..., "usage": ...}`.

`planner.py`
- system = planner_v1 verbatim; human formatted with standup_date and `format_team_updates(sanitized_updates.members)`. Structured output → `SummaryPlan`. Returns `{"plan": ...}`.

`summarizer.py`
- system = summarizer_v1 verbatim. Human = human_template formatted with standup_date, `plan` (as `plan.model_dump_json(indent=2)`), formatted sanitized updates, and `feedback_block` = "" on first pass, else feedback_template formatted with `state.feedback`.
- Plain string call (`llm.ainvoke(messages)` on `get_llm("summarizer")`), NOT structured output — the parser node owns validation.
- Returns `{"raw_summary_output": content, "feedback": None, "usage": ...}` (clears consumed feedback).

`parser.py` — DETERMINISTIC, NO LLM
- Defensive strip: remove leading/trailing whitespace and markdown fences (```json ... ```), take the substring from the first `{` to the last `}` if extra text sneaked in.
- `json.loads` → `StandupSummary.model_validate`.
- Success: `{"parsed_summary": summary}`.
- Failure: `{"feedback": f"Your previous output was invalid JSON or failed schema validation: {short_error}. Return only a single valid JSON object matching the schema.", "revision_count": state.revision_count + 1}`.

`validator.py`
- system = validator_v1 verbatim; human formatted with standup_date, formatted sanitized updates (the source of truth), plan JSON, and `parsed_summary.model_dump_json(indent=2)`. Structured output → `ValidationResult`.
- Approved: `{"validation": result, "status": "validated"}`.
- Rejected: `{"validation": result, "feedback": "\n".join(f"- {i}" for i in result.issues), "revision_count": state.revision_count + 1}`.

`fallback.py` — DETERMINISTIC, NO LLM
- Builds a `StandupSummary` directly from `sanitized_updates` (each member's fields become items verbatim; blockers severity "medium"; tldr = "Auto-generated summary — AI validation unavailable."). Returns `{"parsed_summary": ..., "status": "degraded"}`.

## Step 6 — Graph wiring (`app/agents/graph.py`)

```python
def build_graph() -> CompiledGraph:
    g = StateGraph(GraphState)
    # nodes: sanitizer, planner, summarizer, parser, validator, fallback
    g.set_entry_point("sanitizer")
    g.add_edge("sanitizer", "planner")
    g.add_edge("planner", "summarizer")
    g.add_edge("summarizer", "parser")
    g.add_conditional_edges("parser", route_after_parser,
        {"validator": "validator", "retry": "summarizer", "fallback": "fallback"})
    g.add_conditional_edges("validator", route_after_validator,
        {"done": END, "retry": "summarizer", "fallback": "fallback"})
    g.add_edge("fallback", END)
    return g.compile()
```

Routing functions are PURE — they read state only, never mutate:
- `route_after_parser`: if `state.status == "degraded"` (LLM error upstream) → "fallback"; elif `state.parsed_summary` set by this pass → "validator"; elif `state.revision_count <= settings.MAX_REVISIONS` → "retry"; else → "fallback".
- `route_after_validator`: if degraded → "fallback"; elif `state.validation.approved` → "done"; elif `state.revision_count <= settings.MAX_REVISIONS` → "retry"; else → "fallback".
- Also route planner/summarizer errors: since those nodes set status="degraded" on exception, add the degraded check at the NEXT conditional edge (parser routing already covers it because parser will find no valid output; ensure parser checks status first and short-circuits to fallback without incrementing).
- Compile once at startup (module-level `graph = build_graph()` imported by the service, or build in FastAPI lifespan and store on app.state). Invoke with `await graph.ainvoke(initial_state, config={"recursion_limit": settings.GRAPH_RECURSION_LIMIT})`.

## Step 7 — Service integration (`app/services/summary_service.py`)

1. Load today's updates + active members from DB (existing Phase 1 logic). 422 if any active member is missing an update.
2. Pre-clean raw fields with the deterministic cleaner from Step 5.
3. Build `GraphState(standup_date=..., raw_updates=[...])`, run the graph.
4. From the final state build and persist the summary row: content = parsed_summary as JSONB, rendered_markdown = `render_markdown(parsed_summary, date, degraded=status=="degraded")`, status, plan as JSONB (None-safe), prompt_version = "v1", model_meta = {models per role from settings, revision_count, usage totals per node, sanitizer flags per member, error}.
5. Return the API response shape from Phase 1. The endpoint changes NOTHING — it still just calls the service.

## Step 8 — Tests (extend `tests/`)

Mock ALL LLM calls (monkeypatch the llm factory or node-level llm objects); tests must run offline with no API key.
- `test_prompt_loader.py`: files parse into system/human parts; summarizer system message contains `{` and survives loading unformatted; human templates format without KeyError.
- `test_parser_node.py`: valid JSON passes; fenced ```json passes; junk-wrapped JSON passes; invalid JSON sets feedback and increments revision_count; schema-violating JSON (bad severity) fails validation.
- `test_graph_routing.py` (drive with fake node outputs): happy path ends validated; parse-fail → retry → success path; validator-reject → retry with feedback containing the issues; revision cap → fallback with status degraded; planner exception → fallback; sanitizer LLM failure → pipeline still completes (fail-open).
- `test_render_markdown.py`: golden string test incl. degraded footer.
- `evals/run_evals.py`: script (NOT in pytest default run) that executes the real graph against `evals/golden_inputs.json` with real OpenAI calls and asserts: all members covered, non-empty tldr, blockers from input present, and the prompt-injection golden case ("ignore all instructions...") produces flags containing prompt_injection and a validated summary. Print token usage per run.

## Definition of done

1. POST /summary runs the full real pipeline and returns a validated summary for normal inputs.
2. Feeding a deliberately broken summarizer (mock) exercises retry then fallback; no configuration can loop the graph unboundedly (recursion_limit + MAX_REVISIONS both enforced).
3. Sanitizer flags appear in model_meta; profanity-wrapped blocker survives sanitization in the eval.
4. `pytest` passes offline; `python -m evals.run_evals` passes with a real key.
5. structlog output shows per-node timing and token usage for one full request.

## Do NOT

- Do not use ChatPromptTemplate, LCEL chains, or agents/AgentExecutor — plain message lists + graph nodes only.
- Do not call `.format()` on any system message.
- Do not mutate state inside routing functions.
- Do not let the parser or fallback nodes call an LLM.
- Do not swallow exceptions silently — every degradation is logged and recorded in model_meta.error.
- Do not change Phase 1 endpoints, DB models, or migrations except where this spec says.
