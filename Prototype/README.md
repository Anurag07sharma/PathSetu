# PathSetu prototype: step-by-step build guide

AI-powered patient follow-up system for Indian hospitals.

You have two pieces:

| Folder | What it is | Needs |
|---|---|---|
| `web/pathsetu-demo.html` | The demo you show on stage: hospital follow-up desk + the patient's WhatsApp, fully simulated in the browser | Nothing. Double-click it, or use the published link |
| `backend/` | The real engine behind it: an API that takes AI flags, runs the priority engine, talks to WhatsApp and tracks each patient to "completed" | Python 3.10+, no extra packages |

Build in this order. Each step ends with something you can show.

---

## Step 1. Run and rehearse the stage demo (15 min)

1. Open `web/pathsetu-demo.html` in Chrome.
2. Rehearse this 60-second script:
   - "This is the follow-up desk at a 250-bed hospital in Hanamkonda. The AI reader has flagged 10 scans this month."
   - Click **Ramesh Goud** (P1 Urgent, reader 94% confident). Point at the priority engine: "The reader is confident, so the finding alone sets urgency."
   - Pick **Telugu**, press **Send first message**. The phone shows what Ramesh gets.
   - Answer Yes / No / Yes in the phone. Then **Book this slot**, then **Mark scan as done**.
   - Point at the KPIs: completion rate and revenue recovered both go up.
   - Click **Receive new AI flag**. The new patient's reader is only 68% sure. Answer Yes, Yes, Yes in English: the tier jumps P3 → P1 and a "Second look" tag appears. "That disagreement check comes from our Q-Triage project."
3. Press **Reset demo** before you go on stage.

If the hall Wi-Fi is bad, the file still works offline (only the fonts fall back).

---

## Step 2. Run the backend locally (20 min)

```bash
cd backend
python server.py            # starts on http://localhost:8000, WhatsApp in dry-run mode
```

In a second terminal, send a flag the way an AI reader would:

```bash
curl -X POST localhost:8000/api/flags -d @sample_flag.json
curl localhost:8000/api/worklist
curl localhost:8000/api/metrics
```

In dry-run mode every WhatsApp message is printed in the first terminal, so you can see the full conversation without a Meta account.

Simulate the patient tapping "Yes" on question 1 (replace `PS-1234567` with the id you got back):

```bash
curl -X POST localhost:8000/webhook -d '{"entry":[{"changes":[{"value":{"messages":[{"interactive":{"button_reply":{"id":"ans:PS-1234567:0:1"}}}]}}]}]}'
```

Button ids follow one pattern: `ans:<patient>:<question 0-2>:<1 yes | 0 no>` and `slot:<patient>:book|other|call`.

**Show:** a terminal with the printed Telugu messages + `/api/metrics` going from 0 to 1 completed.

---

## Step 3. Send real WhatsApp messages (1–2 hours, free)

Meta gives every developer a free test number that can message up to 5 verified phones.

1. Go to developers.facebook.com → **Create app** → type **Business** → add the **WhatsApp** product.
2. In **WhatsApp → API Setup** you get a temporary access token, a **Phone number ID**, and a test sender number. Add your 3 team phones as recipients and verify each with the code Meta sends.
3. Set the environment variables and restart the server:
   ```bash
   export WA_TOKEN="<temporary token>"
   export WA_PHONE_NUMBER_ID="<phone number id>"
   export WA_VERIFY_TOKEN="pathsetu-demo"
   python server.py
   ```
4. Expose your laptop so Meta can reach the webhook: `ngrok http 8000` (or `cloudflared tunnel --url http://localhost:8000`). Copy the https URL.
5. In **WhatsApp → Configuration → Webhook**, set Callback URL to `<https url>/webhook` and Verify token to `pathsetu-demo`. Subscribe to the **messages** field.
6. Message the test number once from your phone ("hi"). This opens the 24-hour window, so free-form and button messages can reach you.
7. Send a flag with your own number (country code, no +, e.g. `9198xxxxxxxx`) in `sample_flag.json`. Your phone receives the Telugu message and the Yes/No buttons; tapping them moves the patient through the worklist.

Rules to know for the boardroom:
- Outside the 24-hour window, the first message to a patient **must be an approved template** (Utility category, about ₹0.11 per message in India). Create one named `pathsetu_followup_intro` in WhatsApp Manager and set `WA_INTRO_TEMPLATE=pathsetu_followup_intro`.
- The test number's token expires every 24 hours. For production, create a System User token in Business Settings.

**Show:** a live phone on stage receiving the message when you click a button. Keep the simulated web demo as the backup.

---

## Step 4. Plug in Q-Triage (2–3 hours)

`backend/priority.py` already has the Q-Triage cascade logic in plain Python:

| Q-Triage stage | PathSetu use |
|---|---|
| Classical gatekeeper (confidence ≥ 90%) | AI reader confident → urgency from the finding |
| Quantum committee (3 voters) | 3 patient-risk checks vote: risk model, age + smoking, symptoms |
| Disagreement detection (Tier 4) | Reader unsure but patient risk high → "Second look" by a radiologist |

To use your trained classical models:

1. Clone Q-Triage next to this folder and install its requirements (`pip install -r frontend_package/requirements.txt`).
2. `export QTRIAGE_DIR=/path/to/sih26139-qtriage-Ninth_Quadrant`
3. `priority.qtriage_risk()` loads `models/heart_rf.pkl`. It needs the 6 heart features in Q-Triage's order (age, sex, chest_pain_type, resting_bp_s, max_heart_rate, cholesterol), so send them in the flag as `"vitals": {...}` when the hospital record has them.
4. Apply the same `StandardScaler` Q-Triage used in training before `predict_proba` (it's saved under `data/cleaned/`). Without it, scores will be wrong.
5. Keep the quantum committee out of the live path. Run it offline on a batch and report how often it agrees with the classical model: that is your R&D slide, not a product claim.

The second use, the **return-visit health check**: when a patient comes back for the CT, run Q-Triage's diabetes and heart risk models on the intake form and suggest a consult if the risk is high. That is one extra booking for the hospital.

---

## Step 5. Connect the web demo to the backend (optional, 1–2 hours)

The demo keeps its data in a `patients` array. To make it live:

1. Replace `SEED` with `await (await fetch("http://localhost:8000/api/worklist")).json()` and map fields (`reader_confidence` → `conf`, `severity` → `sev`, stage names → numbers).
2. Make **Mark scan as done** call `POST /api/patients/<id>/complete`.
3. Poll `/api/worklist` every 5 seconds so taps on the real phone appear on the dashboard.

---

## What to say if judges ask "is this real?"

- The web demo is a simulation with fictional patients; the backend runs and sends real WhatsApp messages through Meta's test number.
- The priority engine's patient-risk weights are illustrative. In a pilot we replace them with a model trained on the hospital's own follow-up outcomes.
- PathSetu never diagnoses. It tracks the follow-up the doctor already ordered, which keeps it outside medical-device regulation in its first version.
- The Telugu and Hindi messages need a native-speaker review before real patients see them.
