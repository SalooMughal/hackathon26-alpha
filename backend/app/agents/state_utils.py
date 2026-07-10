"""Coerce LangGraph state to GraphState for node handlers."""

from app.agents.state import GraphState


def as_graph_state(state: GraphState | dict) -> GraphState:
    if isinstance(state, GraphState):
        return state
    return GraphState.model_validate(state)
