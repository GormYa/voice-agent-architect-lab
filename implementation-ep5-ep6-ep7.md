# Implementation Guide — Episodes 5, 6, 7
## Retell AI vs Custom Stack Series

This document maps every **Screen or demo cue** in the ep5, ep6, and ep7 speaking scripts to the
source file it requires. Implement each file so that the described demo can be performed live
during recording without any improvisation. Files are listed in the order they appear on screen.

---

## Repo structure (ep5–ep7 additions)

```
voice-agent-architect-lab/
  ep5-retell-platform/
    retell_agent_config.json   ← exported from Retell dashboard (ep5 s5–s6)
    webhook_handler.py         ← ep5 s7, s8
    lead_qualifier.py          ← called by webhook_handler
    requirements.txt
    README.md

  ep6-retell-custom-backend/
    retell_auth.py             ← ep6 s4
    lead_store.py              ← ep6 s5
    fastapi_app.py             ← ep6 s6, s7, s9
    ghl_webhook.py             ← ep6 s8, s9
    .env.example               ← env var reference for on-screen demo
    requirements.txt
    README.md

  ep7-platform-comparison/
    benchmark.py               ← ep7 s3, s9 (produces the numbers in the slides)
    query_leads.py             ← ep7 s9 (live sqlite3 SELECT during recording)
    results/
      benchmark_results.json  ← pre-run output committed so slide numbers match
    README.md
```

---

## Episode 5

### ep5 / Slide 5 — Greeting Node (Retell dashboard)
**Screen or demo cue:** Switch to Retell dashboard. Show: creating the greeting node, typing the
prompt, adding the "intent" variable, adding the transition.

**Source required:** `ep5-retell-platform/retell_agent_config.json`

The Retell agent must be fully configured in the dashboard before recording.
Export the agent config from Retell (Settings → Export) and commit it as `retell_agent_config.json`
so viewers can import it rather than building from scratch.

Required nodes in the exported config:
- **Greeting** — prompt: `"You are a friendly real estate lead-qualification assistant. Greet the
  caller warmly, introduce yourself as Alex, and ask whether they are looking to buy or sell."`
  Variable: `intent` (string). Transition: `intent is not empty → Qualification`.
- **Qualification** — prompt asks about budget, timeline, location one question at a time.
  Variables: `budget` (string), `timeline` (string), `location` (string).
  Transition A: all three filled → Qualified. Transition B: caller disengages → Not Qualified.
- **Qualified** — prompt: `"Perfect. Let me connect you with one of our agents."` Custom function
  trigger: `POST /retell-webhook`.
- **Not Qualified** — prompt: `"Thanks for your time. I'll send over some resources."` End call.

---

### ep5 / Slide 6 — Conditional Branching (Retell dashboard)
**Screen or demo cue:** Continue screen recording. Show: adding the qualification node, typing the
prompt, adding budget / timeline / location variables, adding the two transitions. Briefly open
the Qualified node and show how simple it is — one prompt line plus the webhook trigger.

**Source required:** same `retell_agent_config.json` as slide 5. No additional file.

Make sure the Qualified node is visible with the custom function endpoint URL already filled in
(`http://localhost:8000/retell-webhook`) before recording — the switch to the webhook handler in
slide 7 should feel like a natural follow-on.

---

### ep5 / Slide 7 — webhook_handler.py (IDE screen recording)
**Screen or demo cue:** Switch to IDE screen recording. Show: `webhook_handler.py`. Walk through
each line slowly. Highlight the validation placeholder and the `response_text` return. Then switch
back to the Retell dashboard to wire up the custom function endpoint.

**Source required:** `ep5-retell-platform/webhook_handler.py`

Requirements:
- Single-file FastAPI app — no imports beyond `fastapi` and `sqlite3`.
- One endpoint: `POST /retell-webhook`.
- Reads `call_id` and `variables` from `await req.json()`.
- Contains a clearly labelled placeholder comment: `# TODO: validate shared secret — see ep6`.
  This placeholder is explicitly called out in the speaking script ("I have a placeholder for that
  here") and must be visible in the IDE recording.
- Calls `store_lead(call_id, variables)` — a function defined in the same file or imported from
  `lead_qualifier.py`.
- Returns `{"response": "Got it. Let me connect you now."}`.
- Must be startable with `uvicorn webhook_handler:app --reload --port 8000` for the live terminal
  in slide 8.

`lead_qualifier.py` (called from `webhook_handler.py`):
- `store_lead(call_id, variables)` — writes one row to a local `leads.db` SQLite file.
- Schema: `(call_id TEXT, variables TEXT, created TEXT)`. No upsert needed in ep5 — that is the
  ep6 improvement.

---

### ep5 / Slide 8 — Live test call (split screen: Retell dashboard + FastAPI terminal)
**Screen or demo cue:** Run the actual Retell dashboard test call on screen. Have FastAPI terminal
visible in a split pane. Show the variable panel updating in real time. Show the webhook POST
arriving in the terminal.

**Source required:** `webhook_handler.py` running. No additional file.

Setup checklist for recording:
- Left pane: Retell dashboard phone simulator, agent loaded, variable panel visible.
- Right pane: `uvicorn webhook_handler:app --reload` terminal. Use `--log-level debug` so the
  incoming POST body is printed.
- Perform the call in this order to make variable extraction visible: state intent → state budget →
  state timeline → state location. Each turn should show a variable update in the Retell panel.
- The webhook POST (with `call_id` and `variables` in the log) must arrive visibly in the terminal
  before the agent speaks its final "Got it" utterance.

---

## Episode 6

### ep6 / Slide 4 — retell_auth.py (IDE screen recording)
**Screen or demo cue:** Show `retell_auth.py` code panel. Walk through each argument to `hmac.new`
slowly — key, msg, digestmod. Highlight `compare_digest` and explain why `==` is wrong.

**Source required:** `ep6-retell-custom-backend/retell_auth.py`

Requirements:
- `RETELL_SECRET = os.environ["RETELL_WEBHOOK_SECRET"]` — env var, never hardcoded.
- `async def verify_retell_signature(request: Request) -> bytes:`
  - Reads `x-retell-signature` header.
  - Calls `await request.body()` — raw bytes, not `request.json()` (JSON parsing mutates the
    byte representation and breaks the signature).
  - Computes `hmac.new(key, msg, hashlib.sha256).hexdigest()`.
  - Compares with `hmac.compare_digest` — the slide speaking script explicitly names this as the
    must-explain line. Add an inline comment: `# constant-time — prevents timing attacks`.
  - Raises `HTTPException(status_code=401)` on mismatch.
  - Returns raw `body` bytes so the caller parses once.
- No other logic in this file — it is shown as a focused, single-responsibility module.

---

### ep6 / Slide 5 — lead_store.py (IDE screen recording)
**Screen or demo cue:** Show `lead_store.py` code panel. Emphasise the `ON CONFLICT` clause. Show
the schema table on the right.

**Source required:** `ep6-retell-custom-backend/lead_store.py`

Requirements:
- `DB_PATH = "leads.db"` constant at module level.
- `init_db()` — creates the `leads` table with `CREATE TABLE IF NOT EXISTS`. Schema exactly:
  `id INTEGER PRIMARY KEY AUTOINCREMENT`, `call_id TEXT UNIQUE`, `variables TEXT`,
  `qualified INTEGER DEFAULT 0`, `created TEXT`.
  `call_id TEXT UNIQUE` is the idempotency key — must be visible to camera.
- `upsert_lead(call_id: str, variables: dict, qualified: bool = False)` — uses
  `INSERT INTO leads ... ON CONFLICT(call_id) DO UPDATE SET variables=..., qualified=...`.
  The `ON CONFLICT` clause is the centrepiece of this slide — it must occupy its own lines,
  not be collapsed to one line.
- `json.dumps(variables)` for the variables column — show the serialisation explicitly.
- `datetime.utcnow().isoformat()` for the created column.
- Call `init_db()` at module import time (not inside a function) so FastAPI's startup event can
  simply `import lead_store`.

---

### ep6 / Slide 6 — fastapi_app.py dynamic injection excerpt (IDE)
**Screen or demo cue:** Show the `fastapi_app.py` excerpt. Highlight the `.get()` calls and the
fallback strings.

**Source required:** `ep6-retell-custom-backend/fastapi_app.py`

Requirements for the main endpoint:
- `@app.post("/retell-webhook")` handler.
- First call: `body = await verify_retell_signature(request)` — shows auth is always first.
- `data = json.loads(body)` — parses after auth, not before.
- `name = data["variables"].get("caller_name", "there")` — the `.get()` with fallback is the
  on-screen teaching point for this slide.
- `appt = data["variables"].get("appointment_time", "soon")` — same pattern.
- `upsert_lead(data["call_id"], data["variables"])` — persists before returning.
- `return {"response": f"Perfect, {name}. Your appointment is confirmed for {appt}."}` — the
  f-string that uses live DB data. This line must be clearly visible as the return value.

---

### ep6 / Slide 7 — fastapi_app.py async pattern (IDE, two panels)
**Screen or demo cue:** Show the two code panels side by side. The wrong pattern should get a
brief moment, then move quickly to the right pattern. Pause on `asyncio.create_task`.

**Source required:** `ep6-retell-custom-backend/fastapi_app.py`

The final handler in `fastapi_app.py` is the "right pattern" version. Add a clearly labelled
block comment above the `create_task` line: `# fire and forget — does not block Retell response`.
The "wrong pattern" does not need to exist as real code — the slide shows it as a labelled
contrast panel. The IDE recording only shows the correct `fastapi_app.py`.

The correct handler must:
- Call `upsert_lead` with `qualified=True` when the qualification custom function is triggered.
- Call `asyncio.create_task(create_ghl_contact(variables))` — the `create_task` call is the
  specific line the speaking script says to pause on.
- Return `{"response": "Connecting you now. One moment."}` immediately after.
- The entire function body from `verify_retell_signature` to the return must fit in one screen
  without scrolling — keep it under 20 lines.

---

### ep6 / Slide 8 — ghl_webhook.py (IDE screen recording)
**Screen or demo cue:** Show `ghl_webhook.py` code panel. Point at the environment variable
references — `GHL_API_KEY`, `GHL_LOCATION_ID`. Show the tags list.

**Source required:** `ep6-retell-custom-backend/ghl_webhook.py`

Requirements:
- `GHL_API_KEY = os.environ["GHL_API_KEY"]` and `GHL_LOCATION_ID = os.environ["GHL_LOCATION_ID"]`
  at module level — both lines visible together so the camera can point at them.
- `GHL_CONTACTS_URL = "https://services.leadconnectorhq.com/contacts/"` — the Lead Connector
  endpoint (not the older API URL).
- `async def create_ghl_contact(variables: dict):` using `httpx.AsyncClient`.
- Headers include `"Version": "2021-07-28"` — GHL requires this header; absence causes silent
  failures. Call it out in a comment.
- Payload maps `caller_name → firstName`, `phone_number → phone`.
- `customFields` list with `budget`, `timeline`, `location` — the list must be visible in full;
  do not collapse it to one line.
- `"tags": ["voice-ai", "qualified-lead"]` — the tags list is explicitly called out in the
  speaking script as the point to show.
- `resp.raise_for_status()` — shown to establish that errors surface rather than silently fail.

---

### ep6 / Slide 9 — End-to-end live test (split screen: Retell dashboard + FastAPI terminal)
**Screen or demo cue:** Run the actual Retell test call with the FastAPI terminal visible. Highlight
the response time in the terminal output. Show the SQLite leads table confirmed. If GHL credentials
available, show the created contact in the GHL dashboard.

**Source required:** all of ep6 running (`fastapi_app.py` with all imports).

Setup checklist for recording:
- `uvicorn fastapi_app:app --reload` running with request timing logged. Add a timing log line:
  `logger.info(f"webhook handled in {elapsed_ms:.0f}ms")` — this is the "47ms" number the
  speaking script references. It must appear in the terminal output.
- After the call, open a second terminal pane and run:
  `sqlite3 leads.db "SELECT call_id, qualified, json_extract(variables, '$.budget') AS budget FROM leads ORDER BY created DESC LIMIT 3;"` — this is the live table confirmation.
- This sqlite3 command should be saved as `ep6-retell-custom-backend/query_leads.sh` so it can
  be run without typing during recording.
- GHL dashboard: if credentials are available, have the GHL Contacts view open in a browser tab.
  Filter by tag `voice-ai` so the new contact is immediately visible after the call.

---

## Episode 7

### ep7 / Slide 3 — benchmark.py (brief terminal view)
**Screen or demo cue:** Show the benchmark setup slide. Read the parameters panel slowly.
(Recording notes: "benchmark terminal output can be shown briefly on screen but the primary medium
is the deck.")

**Source required:** `ep7-platform-comparison/benchmark.py`

Requirements:
- Measures four metrics for the Retell stack: TTFB, extraction latency, webhook RT, cost/call.
- TTFB: time from sending the first user turn to receiving the `response` key in the webhook
  return. Measured by instrumenting `fastapi_app.py` with `time.perf_counter()`.
- Webhook RT: time from Retell firing the custom function to the FastAPI handler returning.
  Retell logs this in the call log; alternatively, log `start = time.perf_counter()` at the top
  of the handler and `elapsed_ms` at the bottom.
- Cost/call: computed from Retell's per-minute rate (configurable constant) × call duration, plus
  API costs if using non-bundled providers.
- Runs 10 iterations of the qualification call script against the ep6 FastAPI server using
  Retell's test call API (or mocked call data).
- Outputs `results/benchmark_results.json` with median values per metric.
- The `benchmark_results.json` values must match the numbers in the ep7 slides exactly:
  TTFB ≈ 730ms, webhook RT ≈ 47ms, cost/call ≈ $0.30 for Retell; ≈ $0.08 for custom.
  If measured values differ, update the slides before recording.

---

### ep7 / Slide 9 — benchmark results (slides + brief terminal)
**Screen or demo cue:** Show the results table. Walk through each row briefly. "Show the SQLite
leads table in a DB browser, or with a quick sqlite3 SELECT, to confirm the row was written."

**Source required:** `ep7-platform-comparison/query_leads.py`

Requirements:
- Simple script that connects to `../ep6-retell-custom-backend/leads.db` and prints a formatted
  table of the last 10 leads with `call_id`, `qualified`, `budget`, `timeline`, `location`, `created`.
- Output must be readable in a terminal at 14pt font — keep line width under 100 chars.
- Run as `python query_leads.py` — no arguments required for the demo.
- Used live during recording after the benchmark call to show the database was written.

---

## .env.example (ep6)

`ep6-retell-custom-backend/.env.example` must list every env var referenced on screen:

```
RETELL_WEBHOOK_SECRET=your_retell_webhook_secret_here
GHL_API_KEY=your_ghl_api_key_here
GHL_LOCATION_ID=your_ghl_location_id_here
```

This file is shown briefly during slide 4 and slide 8 to demonstrate that secrets are never
hardcoded. Keep it as `.env.example` (not `.env`) — never commit live credentials.

---

## requirements.txt files

### ep5-retell-platform/requirements.txt
```
fastapi
uvicorn[standard]
```

### ep6-retell-custom-backend/requirements.txt
```
fastapi
uvicorn[standard]
httpx
python-dotenv
```

### ep7-platform-comparison/requirements.txt
```
httpx
python-dotenv
tabulate
```

---

## Pre-recording checklist (all three episodes)

### Before recording ep5
- [ ] Retell agent fully configured in dashboard; test call passes end-to-end in simulator
- [ ] `webhook_handler.py` starts without error on `uvicorn webhook_handler:app --reload --port 8000`
- [ ] TODO validation comment is visible in IDE at the default font size
- [ ] Retell custom function URL set to `http://localhost:8000/retell-webhook` (use ngrok if needed)

### Before recording ep6
- [ ] `.env` populated (from `.env.example`); never shown on screen
- [ ] `uvicorn fastapi_app:app --reload` starts without import errors
- [ ] One end-to-end call test passes: leads.db written, GHL contact created
- [ ] Timing log line (`webhook handled in Xms`) visible in terminal output
- [ ] `query_leads.sh` tested — runs in < 1 second and returns readable output
- [ ] GHL Contacts view filtered by `voice-ai` tag and visible in browser

### Before recording ep7
- [ ] `benchmark.py` has been run; `results/benchmark_results.json` committed
- [ ] Slide numbers (TTFB, cost/call) match `benchmark_results.json` values exactly
- [ ] `query_leads.py` tested against a populated `leads.db`
- [ ] Decision framework flowchart rehearsed — all four paths traceable without reading the slide

---

## File-to-script-cue mapping (quick reference)

| File | Episode | Slide | Cue summary |
| --- | --- | --- | --- |
| `retell_agent_config.json` | ep5 | s5, s6 | Dashboard walkthrough — import this to recreate the agent |
| `webhook_handler.py` | ep5 | s7 | IDE recording — show full file, highlight TODO comment + response return |
| `webhook_handler.py` running | ep5 | s8 | Terminal pane — show POST arriving with variables |
| `retell_auth.py` | ep6 | s4 | IDE recording — walk through hmac.new args + compare_digest |
| `lead_store.py` | ep6 | s5 | IDE recording — emphasise ON CONFLICT clause |
| `fastapi_app.py` (injection) | ep6 | s6 | IDE recording — highlight .get() fallback pattern |
| `fastapi_app.py` (async) | ep6 | s7 | IDE recording — pause on asyncio.create_task line |
| `ghl_webhook.py` | ep6 | s8 | IDE recording — point at env vars + tags list |
| all ep6 running | ep6 | s9 | Split screen — terminal timing log + sqlite3 SELECT |
| `benchmark.py` output | ep7 | s3 | Brief terminal — validates benchmark methodology |
| `query_leads.py` | ep7 | s9 | Terminal — confirms SQLite rows after benchmark run |
