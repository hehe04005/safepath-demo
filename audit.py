"""Append-only audit log and the human-checkpoint functions.

These human-action functions live outside the graphs on purpose: the graphs
can only draft a suggestion/alert/booking, never commit one. Only these
functions -- triggered by an explicit human click in app.py -- write a
"confirmed" decision to the log.
"""

from datetime import datetime

AUDIT_LOG = []


def log_action(actor: str, action: str, detail: str = "") -> None:
    AUDIT_LOG.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "actor": actor,
        "action": action,
        "detail": detail,
    })


def staff_confirm(result: dict) -> str:
    if result["status"] == "drafted":
        log_action("staff", "confirmed", result["suggestion"])
        return f"Registered to {result['department_guess']} (confirmed by staff)."
    log_action("staff", "acknowledged_escalation", result.get("chief_complaint", ""))
    return "Emergency escalation acknowledged by staff."


def staff_reject(result: dict) -> str:
    log_action("staff", "rejected", result.get("suggestion", ""))
    return "Staff rejected the draft; will register manually."


def pharmacist_decide(result: dict, dispense: bool) -> str:
    action = "confirmed_override" if dispense else "withheld"
    log_action("pharmacist", action, result.get("alert_text", ""))
    return "Dispensed (override logged)." if dispense else "Withheld pending doctor review."


def staff_confirm_booking(result: dict) -> str:
    log_action("staff", "confirmed_booking", f"day +{result.get('booked_day')}")
    return "Follow-up booked (confirmed by staff)."
