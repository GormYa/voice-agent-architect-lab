# EP2 Telephony Bridge

Twilio bridge patterns: Mu-law conversion, echo cancellation, and relay payload design.

## Live Demo (Slide 6)

### 1) Start server without AEC

```powershell
cd C:\Users\oguz\source\repos\voice-agent-architect-lab
.venv313\Scripts\Activate.ps1
cd ep2-telephony-bridge
$env:AEC_ENABLED="0"
$env:PUBLIC_WS_URL="wss://<your-ngrok-domain>/twilio/media"
python -m uvicorn demo_twilio_server:app --host 0.0.0.0 --port 8022
```

### 2) Expose local server to Twilio

```powershell
ngrok http 8022
```

Use the generated https domain in Twilio webhook:
- Voice webhook URL: `https://<your-ngrok-domain>/twilio/voice` (HTTP POST)

### 3) Place first call (AEC OFF)

- Call your Twilio number.
- Speak a test phrase while agent audio is active.
- Show `logs/call_transcripts.jsonl` entries for echo artifacts.

### 4) Restart with AEC ON

```powershell
$env:AEC_ENABLED="1"
python -m uvicorn demo_twilio_server:app --host 0.0.0.0 --port 8022
```

- Place same call again with same test phrase.
- Show `suppressed`, `correlation`, and cleaner transcript rows in JSONL.
- Print per-call metrics:

```powershell
python summarize_logs.py
```

### 5) Terminal-only fallback

```powershell
python demo_aec.py
```
