"""LangGraph workflow — graph wiring and conditional edges in Phase 2."""

from langgraph.graph import END, StateGraph

from app.agents.nodes.parser import parser_node
from app.agents.nodes.planner import planner_node
from app.agents.nodes.summarizer import summarizer_node
from app.agents.nodes.validator import validator_node
from app.agents.state import GraphState


def build_graph():
    """Compile the standup summary LangGraph. Full edge logic in Phase 2."""
    graph = StateGraph(GraphState)
    graph.add_node("planner", planner_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("parser", parser_node)
    graph.add_node("validator", validator_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "summarizer")
    graph.add_edge("summarizer", "parser")
    graph.add_edge("parser", "validator")
    graph.add_edge("validator", END)

    return graph.compile()
