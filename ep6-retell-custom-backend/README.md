# EP6 Retell Custom Backend

Signed Retell webhook handling, idempotent lead storage, and asynchronous GHL
contact creation.

## Setup

```powershell
cd ep6-retell-custom-backend
copy .env.example .env
```

Populate `.env` before running the server.

## Run

```powershell
uvicorn fastapi_app:app --reload --port 8000
```

After a call, confirm recent qualified leads:

```powershell
bash query_leads.sh
```

The app logs `webhook handled in Xms` for the terminal timing cue.
