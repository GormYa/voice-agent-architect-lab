from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

LOG_PATH = Path("logs/call_transcripts.jsonl")


def main() -> None:
    if not LOG_PATH.exists():
        print(f"No log file at {LOG_PATH}")
        return

    calls: dict[str, dict] = {}
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            sid = row.get("stream_sid", "unknown")
            c = calls.setdefault(sid, {
                "aec_enabled": None,
                "inbound": 0,
                "suppressed": 0,
                "correlations": [],
                "echo_artifacts": 0,
            })
            if row.get("event") == "start":
                c["aec_enabled"] = row.get("aec_enabled")
            if row.get("event") == "media" and row.get("track") == "inbound":
                c["inbound"] += 1
                if row.get("suppressed"):
                    c["suppressed"] += 1
                corr = row.get("correlation")
                if isinstance(corr, (int, float)):
                    c["correlations"].append(float(corr))
                if row.get("stt_text") == "i need help help help":
                    c["echo_artifacts"] += 1

    print("Per-call summary")
    for sid, c in sorted(calls.items()):
        inbound = c["inbound"] or 1
        suppression_rate = c["suppressed"] / inbound
        avg_corr = mean(c["correlations"]) if c["correlations"] else 0.0
        print(
            f"{sid} | AEC={c['aec_enabled']} | inbound={c['inbound']} | "
            f"suppression_rate={suppression_rate:.2%} | avg_corr={avg_corr:.3f} | "
            f"echo_artifacts={c['echo_artifacts']}"
        )


if __name__ == "__main__":
    main()
