# voice-agent-architect-lab

Production-leaning Voice AI engineering patterns across four episodes.

## Episodes

1. `ep1-realtime-tts` - FastAPI + ElevenLabs-style bidirectional streaming scaffolding with latency instrumentation.
2. `ep2-telephony-bridge` - Twilio Media Stream and ConversationRelay architecture patterns (Mu-law, AEC, routing).
3. `ep3-voice-design` - Vision-informed voice persona design and multi-voice session switching.
4. `ep4-langgraph-orchestration` - Stateful orchestration with interrupt handling, speculative execution, and semantic caching.

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
python ep3-voice-design\demo\statue_demo.py
python ep4-langgraph-orchestration\graph\supervisor.py
```
