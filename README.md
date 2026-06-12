# voice-agent-architect-lab

Production-leaning Voice AI engineering patterns across seven episodes.

## Episodes

1. `ep1-realtime-tts` - FastAPI + ElevenLabs-style bidirectional streaming scaffolding with latency instrumentation.
2. `ep2-telephony-bridge` - Twilio Media Stream and ConversationRelay architecture patterns (Mu-law, AEC, routing).
3. `ep3-voice-design` - Vision-informed voice persona design and multi-voice session switching.
4. `ep4-langgraph-orchestration` - Stateful orchestration with interrupt handling, speculative execution, and semantic caching.
5. `ep5-retell-platform` - Retell dashboard import config plus a minimal lead-qualification webhook.
6. `ep6-retell-custom-backend` - Signed Retell webhook verification, idempotent SQLite storage, and async GHL sync.
7. `ep7-platform-comparison` - Deterministic benchmark output and lead-table query helpers for comparison slides.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Tests

```bash
pytest -q
```

## Run samples

```bash
uvicorn ep1-realtime-tts.server:app --reload
python ep2-telephony-bridge\bridge\media_stream.py
python ep3-voice-design\demo\statue_demo.py path\to\statue.jpg --classify-only
python ep3-voice-design\demo\voice_design_demo.py
python ep3-voice-design\demo\full_pipeline_demo.py path\to\statue.jpg path\to\portrait.jpg path\to\artifact.jpg --play
python ep4-langgraph-orchestration\graph\supervisor.py
cd ep5-retell-platform && uvicorn webhook_handler:app --reload --port 8000
cd ep6-retell-custom-backend && uvicorn fastapi_app:app --reload --port 8000
python ep7-platform-comparison\benchmark.py
python ep7-platform-comparison\query_leads.py
```
