"""Shared state definitions for each LangGraph stage."""

from typing import TypedDict, Optional


class Stage0State(TypedDict):
    symptom_text: str
    chief_complaint: str
    red_flag: bool
    department_guess: str
    status: str
    suggestion: Optional[str]


class Stage3State(TypedDict):
    patient_id: str
    new_medication: str
    conflict: Optional[dict]
    status: str
    alert_text: Optional[str]


class Stage4State(TypedDict):
    doctor_id: str
    window_start: int
    window_end: int
    booked_day: Optional[int]
    status: str
