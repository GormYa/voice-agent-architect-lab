from fastapi import FastAPI, Request

from lead_qualifier import store_lead


app = FastAPI(title="EP5 Retell Webhook")


@app.post("/retell-webhook")
async def retell_webhook(req: Request):
    payload = await req.json()
    print({"retell_webhook_payload": payload})

    call_id = payload.get("call_id")
    variables = payload.get("variables", {})

    # TODO: validate shared secret — see ep6
    store_lead(call_id, variables)

    return {"response": "Got it. Let me connect you now."}
