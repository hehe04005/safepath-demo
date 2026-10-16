"""Node functions for each LangGraph stage, plus Stage 1 (plain functions, no graph).

Stage 1 (checkpoint navigation) is deliberately not a LangGraph graph -- it is a
single scan -> check-elapsed-time -> advance-or-escalate cycle, with no branching
into knowledge retrieval, so a graph would add structure without adding clarity.
Stage 0 and Stage 3 are graphs because they branch into RAG-grounded reasoning.
"""

from state import Stage0State, Stage3State, Stage4State
from tools import extract_symptoms, retrieve_department, check_conflict, find_slot, CHECKPOINT_DIRECTIONS, llm_triage_suggestion
from audit import log_action


# --- Stage 0: symptom triage ---

def extract_node(state: Stage0State) -> dict:
    return extract_symptoms(state["symptom_text"])


def route_stage0(state: Stage0State) -> str:
    return "escalate" if state["red_flag"] else "triage"


def escalate_node(state: Stage0State) -> dict:
    log_action("agent", "escalated", state["chief_complaint"])
    return {"status": "escalated_emergency", "suggestion": None}


def triage_node(state: Stage0State) -> dict:
    candidates = retrieve_department(state["chief_complaint"], top_k=3)
    llm_result = llm_triage_suggestion(state["chief_complaint"], candidates)
    if llm_result is not None:
        suggestion = f"Suggest {llm_result.department} (cite {llm_result.cited_guideline_id}): {llm_result.reasoning}"
        log_action("agent", "draft_suggestion_llm", suggestion)
    else:
        # Fallback: Gemini call failed (network, quota, bad key) -- degrade to
        # the deterministic top-1 TF-IDF template rather than crash or leave
        # the patient with no suggestion at all.
        top = candidates[0]
        suggestion = f"Suggest {top['department']} (cite {top['id']}: \"{top['text']}\") [fallback: LLM unavailable]"
        log_action("agent", "draft_suggestion_fallback", suggestion)
    return {"status": "drafted", "suggestion": suggestion}


# --- Stage 3: medication safety check ---

def check_node(state: Stage3State) -> dict:
    return {"conflict": check_conflict(state["patient_id"], state["new_medication"])}


def route_stage3(state: Stage3State) -> str:
    return "conflict" if state["conflict"] else "clear"


def alert_node(state: Stage3State) -> dict:
    rule = state["conflict"]
    alert_text = f"Potential conflict: {rule['text']} (cite {rule['id']})"
    log_action("agent", "draft_pharmacist_alert", alert_text)
    return {"status": "drafted_alert", "alert_text": alert_text}


def clear_node(state: Stage3State) -> dict:
    log_action("agent", "no_conflict", f"{state['new_medication']} cleared")
    return {"status": "no_conflict", "alert_text": None}


# --- Stage 4: follow-up booking ---

def reason_match_node(state: Stage4State) -> dict:
    slot = find_slot(state["doctor_id"], state["window_start"], state["window_end"])
    return {"booked_day": slot}


def route_stage4(state: Stage4State) -> str:
    return "booked" if state["booked_day"] is not None else "conflict"


def draft_booking_node(state: Stage4State) -> dict:
    log_action("agent", "draft_followup_booking", f"day +{state['booked_day']} with {state['doctor_id']}")
    return {"status": "drafted_booking"}


def surface_conflict_node(state: Stage4State) -> dict:
    log_action("agent", "roster_conflict", f"no slot with {state['doctor_id']} in window")
    return {"status": "conflict_needs_staff"}


# --- Stage 1: checkpoint tracker (plain perceive-reason-act, no graph) ---

CHECKPOINTS = ["check_in", "consult_room", "cashier", "pharmacy"]
TIMEOUT_MINUTES = 15  # simulated minutes, not real wall-clock time


def start_journey(patient_id: str, mobility_assist: bool = False) -> dict:
    log_action("agent", "checkpoint_scan", f"{patient_id} started at {CHECKPOINTS[0]}")
    return {
        "patient_id": patient_id,
        "checkpoint_index": 0,
        "escalated": False,
        "mobility_assist": mobility_assist,
    }


def scan_next(journey: dict, minutes_since_last_scan: int) -> dict:
    if minutes_since_last_scan > TIMEOUT_MINUTES:
        journey["escalated"] = True
        log_action("agent", "timeout_escalation",
                    f"{minutes_since_last_scan} min since last checkpoint "
                    f"(last known: {CHECKPOINTS[journey['checkpoint_index']]})")
        return journey

    next_index = journey["checkpoint_index"] + 1
    if next_index < len(CHECKPOINTS):
        journey["checkpoint_index"] = next_index
        log_action("agent", "checkpoint_scan", CHECKPOINTS[next_index])
    return journey


def current_guidance(journey: dict, route_override: str = None) -> str:
    """route_override lets the UI show the other (standard/accessible) route
    for the same checkpoint without changing the patient's stored preference
    -- the "show the other route" button, not a real live-traffic reroute."""
    if journey["escalated"]:
        return "A volunteer has been notified and is on the way."
    idx = journey["checkpoint_index"]
    if idx + 1 >= len(CHECKPOINTS):
        return "Visit complete. Please collect your medicine."
    next_checkpoint = CHECKPOINTS[idx + 1]
    route = route_override or ("accessible" if journey.get("mobility_assist") else "standard")
    directions = CHECKPOINT_DIRECTIONS.get(next_checkpoint)
    if directions:
        return directions[route]
    return f"Please proceed to: {next_checkpoint.replace('_', ' ').title()}"
