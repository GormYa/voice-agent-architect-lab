# EP5 Retell Platform

Dashboard-first Retell agent setup plus the smallest webhook needed for a live
lead-qualification demo.

## Files to show

1. `retell_agent_config.json` - import this into Retell to recreate the
   Greeting, Qualification, Qualified, and Not Qualified nodes.
2. `webhook_handler.py` - FastAPI endpoint for the Retell custom function.
3. `lead_qualifier.py` - local SQLite write for the qualified lead.

## Run

```powershell
cd ep5-retell-platform
uvicorn webhook_handler:app --reload --port 8000 --log-level debug
```

The webhook stores rows in `leads.db` with `call_id`, serialized `variables`,
and `created`.
