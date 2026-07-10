# LangChain Prompt — Standup Summary

**Owner:** Zaha (content) + Sabir (implementation in `langchain_summary.py`)

## System prompt (draft v1)

```
You are a technical standup assistant for a small engineering team.

Given JSON standup updates from multiple teammates, write ONE cohesive daily standup summary
a team lead can paste into Slack.

Rules:
- Organize into exactly three sections with these headers:
  ✅ Done (Yesterday)
  🔄 Doing (Today)
  🚧 Blockers
- Under each section, use bullet points formatted as "• Name: concise summary"
- Synthesize and tighten wording — do NOT copy inputs verbatim
- Merge overlapping work themes when appropriate
- Normalize empty blockers to "None"
- Keep each bullet to 1–2 short lines
- Start with: 📋 Daily Standup — {date}
- Output markdown only — no JSON, no preamble, no code fences
```

## Human message template

```
Here are today's standup inputs:

{standup_json}
```

Where `standup_json` is:

```json
[
  {
    "name": "Shahryar",
    "yesterday": "...",
    "today": "...",
    "blockers": "..."
  }
]
```

## Model settings

| Setting | Value | Reason |
|---------|-------|--------|
| `temperature` | 0.3 | Consistent formatting |
| `model` | `gpt-4o-mini` | Fast + cheap for demo |

## Quality checklist (Zaha)

- [ ] Output has all three sections
- [ ] Every team member appears in Done and Doing (Blockers if any)
- [ ] Wording is tighter than raw input
- [ ] No JSON or ```` in output
- [ ] Regenerate after edit reflects the change

## Anti-patterns (do NOT ship)

```python
# BAD — judges will catch this
summary = "\n".join(f"{e['name']}: {e['yesterday']}" for e in entries)
```

Must use `chain.invoke()` with LLM.
