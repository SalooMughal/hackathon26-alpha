"""LangGraph standup summary workflow with bounded revision loops."""

from langgraph.graph import END, StateGraph

from app.agents.nodes.fallback import fallback_node
from app.agents.nodes.parser import parser_node
from app.agents.nodes.planner import planner_node
from app.agents.nodes.sanitizer import sanitizer_node
from app.agents.nodes.summarizer import summarizer_node
from app.agents.nodes.validator import validator_node
from app.agents.state import GraphState
from app.agents.state_utils import as_graph_state
from app.core.config import get_settings


def route_after_parser(state: GraphState | dict) -> str:
    s = as_graph_state(state)
    if s.status == "degraded":
        return "fallback"
    if s.parsed_summary is not None:
        return "validator"
    settings = get_settings()
    if s.revision_count <= settings.MAX_REVISIONS:
        return "retry"
    return "fallback"


def route_after_validator(state: GraphState | dict) -> str:
    s = as_graph_state(state)
    if s.status == "degraded":
        return "fallback"
    if s.validation and s.validation.approved:
        return "done"
    settings = get_settings()
    if s.revision_count <= settings.MAX_REVISIONS:
        return "retry"
    # Exhausted retries but we have an AI-parsed summary — use it instead of raw fallback.
    if s.parsed_summary is not None and s.parsed_summary.tldr != (
        "Auto-generated summary — AI validation unavailable."
    ):
        return "done"
    return "fallback"


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("sanitizer", sanitizer_node)
    graph.add_node("planner", planner_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("parser", parser_node)
    graph.add_node("validator", validator_node)
    graph.add_node("fallback", fallback_node)

    graph.set_entry_point("sanitizer")
    graph.add_edge("sanitizer", "planner")
    graph.add_edge("planner", "summarizer")
    graph.add_edge("summarizer", "parser")
    graph.add_conditional_edges(
        "parser",
        route_after_parser,
        {"validator": "validator", "retry": "summarizer", "fallback": "fallback"},
    )
    graph.add_conditional_edges(
        "validator",
        route_after_validator,
        {"done": END, "retry": "summarizer", "fallback": "fallback"},
    )
    graph.add_edge("fallback", END)
    return graph.compile()


graph = build_graph()
