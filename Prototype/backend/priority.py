"""PathSetu priority engine.

Adapts the Q-Triage confidence cascade (classical gatekeeper -> committee vote ->
disagreement check) to a new question: how hard and how fast should we chase this
follow-up?  It never diagnoses; the AI reader and the doctor already flagged the scan.

Tiers
  P1 Urgent  - navigator calls within 24 h and books the slot
  P2 High    - WhatsApp + voice call, book within 7 days
  P3 Routine - WhatsApp reminders, book within 30 days
"""
import math
import os

ACTIONS = {
    "P1": "Navigator calls within 24 h and books the slot",
    "P2": "WhatsApp + voice call, book within 7 days",
    "P3": "WhatsApp reminders, book within 30 days",
}
READER_CONFIDENT = 0.90   # same cut-off as Q-Triage's classical gatekeeper
SECOND_LOOK_BELOW = 0.80


def patient_risk(age, answers):
    """Illustrative logistic score from the three WhatsApp questions.

    Replace with a model trained on your own follow-up outcomes once a pilot
    hospital shares data, or with Q-Triage's classical models (see qtriage_risk).
    """
    a = answers or {}
    z = -3 + 0.045 * (age - 40) + 1.0 * a.get("smoke", False) + 0.6 * a.get("sugar", False) + 1.2 * a.get("cough", False)
    return 1 / (1 + math.exp(-z))


def compute(p):
    """p: dict with age, finding, severity (1-3), reader_confidence (0-1), answers (dict or None)."""
    answers = p.get("answers") or {}
    conf, sev = p["reader_confidence"], p["severity"]
    risk = qtriage_risk(p)
    if risk is None:
        risk = patient_risk(p["age"], answers)

    # Stage 1: classical gatekeeper. A confident reader -> urgency comes from the finding itself.
    if conf >= READER_CONFIDENT:
        tier = {3: "P1", 2: "P2"}.get(sev, "P3")
        return dict(tier=tier, action=ACTIONS[tier], second_look=False, risk=round(risk, 3),
                    path="reader_confident", votes=None)

    # Stage 2: committee of three independent patient-risk checks.
    votes = {
        "risk_model": risk >= 0.5,
        "age_and_smoking": p["age"] >= 50 and answers.get("smoke", False),
        "symptoms": answers.get("cough", False) or (answers.get("sugar", False) and "TB" in p["finding"]),
    }
    high = sum(votes.values())
    if high == 3:
        tier = "P1"
    elif high == 2 or (high == 1 and sev >= 2) or sev == 3:
        tier = "P2"
    else:
        tier = "P3"

    # Stage 3: disagreement check (Q-Triage's "paradigm divergence" tier, re-used).
    second_look = high >= 2 and conf < SECOND_LOOK_BELOW
    return dict(tier=tier, action=ACTIONS[tier], second_look=second_look, risk=round(risk, 3),
                path="committee", votes=votes)


# ---------------------------------------------------------------------------
# Optional: plug in Q-Triage. Set QTRIAGE_DIR to your cloned Q-Triage repo.
# Step 4 of README.md explains the feature mapping.
# ---------------------------------------------------------------------------
_QT = {"loaded": False, "models": {}}


def _load_qtriage():
    _QT["loaded"] = True
    root = os.environ.get("QTRIAGE_DIR")
    if not root:
        return
    try:
        import joblib  # noqa: installed with Q-Triage's requirements
        for name in ("heart_rf", "diabetes_xgb"):
            path = os.path.join(root, "models", f"{name}.pkl")
            if os.path.exists(path):
                _QT["models"][name] = joblib.load(path)
    except Exception as exc:  # keep PathSetu running even if Q-Triage fails to load
        print(f"[priority] Q-Triage not loaded: {exc}")


def qtriage_risk(p):
    """Return a 0-1 risk from Q-Triage's classical heart model, or None to use the fallback.

    Q-Triage's heart RF expects 6 features in this order (see its CONTEXT.md):
    age, sex, chest_pain_type, resting_bp_s, max_heart_rate, cholesterol.
    PathSetu only has what it collects on WhatsApp, so this hook fires only when the
    hospital record supplies the vitals in p["vitals"].
    """
    if not _QT["loaded"]:
        _load_qtriage()
    model = _QT["models"].get("heart_rf")
    v = p.get("vitals")
    if model is None or not v:
        return None
    try:
        import numpy as np
        x = np.array([[p["age"], 1 if p.get("sex") == "M" else 0, v["chest_pain_type"],
                       v["resting_bp"], v["max_heart_rate"], v["cholesterol"]]], dtype=float)
        # NOTE: apply the same StandardScaler Q-Triage used in training before predict_proba.
        return float(model.predict_proba(x)[0][1])
    except Exception as exc:
        print(f"[priority] Q-Triage scoring failed, using fallback: {exc}")
        return None
