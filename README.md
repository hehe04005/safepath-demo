# SafePath — Prototype Source Code

CA6117 Agentic AI in Healthcare, Group 19 (ZHAOYIHE, G2510990J; WANGXICHUN, G2509340H).

SafePath is a guardrail-bounded agent that walks an elderly patient through a
hospital visit (intake/triage, checkpoint navigation, consultation,
medication safety check, follow-up booking) while keeping every committing
action — registering, dispensing, booking — behind an explicit human
checkpoint. Full design rationale, architecture, and evaluation are in the
written report; this README covers only how to run the code.

## 1. Requirements

- Python 3.11+ (developed and tested on Python 3.13).
- No external services required to run the demo — see "Mock mode" below.

## 2. Setup

```bash
cd safepath
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Exact dependency versions used during development/testing are pinned in
`requirements.txt` (streamlit, langgraph, google-genai, python-dotenv,
scikit-learn, pydantic).

## 3. Run

```bash
streamlit run app.py
```

This opens the dashboard in your browser (default `http://localhost:8501`).
Use the sidebar to pick a simulated patient and step through the five
stages (Intake & Triage → Checkpoint Navigation → Visit & Consultation →
Medication Safety Check → Follow-up Booking) plus the Audit Log viewer.

## 4. Mock mode vs. live Gemini mode (LLM configuration)

The app runs in two modes, controlled entirely by whether a Gemini API key
is present:

- **Mock mode (default, no setup needed)** — if no API key is configured,
  `llm_triage_suggestion()` in `tools.py` simply never succeeds in calling
  Gemini, and the Stage 0 triage node falls back to its deterministic,
  rule-based top-1 guideline match. The rest of the app (checkpoint
  navigation, medication conflict checks, roster lookup, audit log) does
  not call any LLM at all and is unaffected. **A grader can run the full
  demo with zero configuration.**
- **Live Gemini mode (optional)** — to see the LLM-grounded triage
  suggestion path instead of the fallback, create a file named `.env` in
  this folder (same directory as `app.py`) containing:

  ```
  GEMINI_API_KEY=your_own_key_here
  ```

  `tools.py` loads this automatically via `python-dotenv` on startup. Get a
  key from [Google AI Studio](https://aistudio.google.com/). No other
  environment variables are required.

  Note: our own `.env` file (with our development key) is intentionally
  **not** included in this submission — each key is personal/billable, so
  grading/demo should use mock mode, or a grader's own key if they want to
  exercise the live path.

## 5. File map

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI — the 5-stage dashboard + Audit Log viewer. Entry point. |
| `state.py` | TypedDict state schemas for the three LangGraph stages. |
| `tools.py` | Simulated data sources, the two RAG lookups (TF-IDF + cosine similarity), and the Gemini LLM call. |
| `nodes.py` | One node function per graph step, plus Stage 1's plain perceive→reason→act functions. |
| `graph.py` | Assembles `stage0_app`, `stage3_app`, `stage4_app` with LangGraph's `StateGraph`. |
| `audit.py` | Append-only audit log and the four human-checkpoint functions (`staff_confirm`, `staff_reject`, `pharmacist_decide`, `staff_confirm_booking`) — the only functions that write a "confirmed" decision. |
| `ui.py` | Earlier UI exploration, kept for reference; not imported by `app.py`. |
| `assets/` | Static image(s) used by the Streamlit UI. |

## 6. Deployment note

This prototype is a local Streamlit app (no separate backend/database —
all "services" are simulated in-process per the project brief). To let a
grader try it without local setup, it can also be deployed for free on
[Streamlit Community Cloud](https://streamlit.io/cloud) by pointing it at
this folder's `app.py`; we have not pre-deployed a public build as part of
this submission.
