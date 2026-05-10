from __future__ import annotations


def inbound_twiml(ws_url: str) -> str:
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
  <Connect>
    <Stream url=\"{ws_url}\" />
  </Connect>
</Response>"""
