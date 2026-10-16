"""Assemble each stage's LangGraph graph from the node functions in nodes.py."""

from langgraph.graph import StateGraph, END

from state import Stage0State, Stage3State, Stage4State
from nodes import (
    extract_node, route_stage0, escalate_node, triage_node,
    check_node, route_stage3, alert_node, clear_node,
    reason_match_node, route_stage4, draft_booking_node, surface_conflict_node,
)


def _build_stage0():
    g = StateGraph(Stage0State)
    g.add_node("extract", extract_node)
    g.add_node("escalate", escalate_node)
    g.add_node("triage", triage_node)
    g.set_entry_point("extract")
    g.add_conditional_edges("extract", route_stage0, {"escalate": "escalate", "triage": "triage"})
    g.add_edge("escalate", END)
    g.add_edge("triage", END)
    return g.compile()


def _build_stage3():
    g = StateGraph(Stage3State)
    g.add_node("check", check_node)
    g.add_node("alert", alert_node)
    g.add_node("clear", clear_node)
    g.set_entry_point("check")
    g.add_conditional_edges("check", route_stage3, {"conflict": "alert", "clear": "clear"})
    g.add_edge("alert", END)
    g.add_edge("clear", END)
    return g.compile()


def _build_stage4():
    g = StateGraph(Stage4State)
    g.add_node("reason_match", reason_match_node)
    g.add_node("draft_booking", draft_booking_node)
    g.add_node("surface_conflict", surface_conflict_node)
    g.set_entry_point("reason_match")
    g.add_conditional_edges("reason_match", route_stage4, {"booked": "draft_booking", "conflict": "surface_conflict"})
    g.add_edge("draft_booking", END)
    g.add_edge("surface_conflict", END)
    return g.compile()


stage0_app = _build_stage0()
stage3_app = _build_stage3()
stage4_app = _build_stage4()
