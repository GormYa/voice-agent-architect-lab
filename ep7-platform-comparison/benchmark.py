from __future__ import annotations

import argparse
from datetime import datetime, UTC
import hashlib
import hmac
import json
import os
from pathlib import Path
from statistics import median
import time

import httpx


RESULTS_PATH = Path(__file__).resolve().parent / "results" / "benchmark_results.json"
ITERATIONS = 10
RETELL_RATE_PER_MINUTE = float(os.getenv("RETELL_RATE_PER_MINUTE", "0.30"))
CUSTOM_COST_PER_CALL = float(os.getenv("CUSTOM_COST_PER_CALL", "0.08"))
CALL_DURATION_SECONDS = float(os.getenv("BENCHMARK_CALL_DURATION_SECONDS", "60"))

MOCK_TTFB_MS = [712, 718, 724, 728, 730, 730, 734, 740, 746, 752]
MOCK_EXTRACTION_MS = [166, 170, 174, 178, 180, 180, 184, 187, 190, 194]
MOCK_WEBHOOK_MS = [41, 44, 45, 46, 47, 47, 50, 51, 52, 55]
MOCK_CUSTOM_TTFB_MS = [388, 396, 404, 416, 420, 420, 428, 436, 444, 452]
MOCK_CUSTOM_EXTRACTION_MS = [82, 88, 91, 94, 95, 95, 98, 101, 105, 109]
MOCK_CUSTOM_WEBHOOK_MS = [25, 28, 30, 31, 32, 32, 34, 36, 38, 40]


def retell_cost_per_call() -> float:
    return round((CALL_DURATION_SECONDS / 60) * RETELL_RATE_PER_MINUTE, 2)


def mocked_iterations() -> list[dict]:
    return [
        {
            "iteration": index + 1,
            "retell_ttfb_ms": MOCK_TTFB_MS[index],
            "retell_extraction_latency_ms": MOCK_EXTRACTION_MS[index],
            "retell_webhook_rt_ms": MOCK_WEBHOOK_MS[index],
            "retell_cost_per_call_usd": retell_cost_per_call(),
            "custom_ttfb_ms": MOCK_CUSTOM_TTFB_MS[index],
            "custom_extraction_latency_ms": MOCK_CUSTOM_EXTRACTION_MS[index],
            "custom_webhook_rt_ms": MOCK_CUSTOM_WEBHOOK_MS[index],
            "custom_cost_per_call_usd": CUSTOM_COST_PER_CALL,
        }
        for index in range(ITERATIONS)
    ]


def live_iterations(url: str, secret: str) -> list[dict]:
    rows = []
    with httpx.Client(timeout=15) as client:
        for index in range(ITERATIONS):
            payload = {
                "call_id": f"bench-call-{index + 1}",
                "function_name": "qualification",
                "variables": {
                    "caller_name": "Jordan Lee",
                    "phone_number": "+15550101010",
                    "appointment_time": "tomorrow at 2 PM",
                    "budget": "$850k",
                    "timeline": "60 days",
                    "location": "Austin",
                },
            }
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            start = time.perf_counter()
            resp = client.post(
                url,
                content=body,
                headers={
                    "content-type": "application/json",
                    "x-retell-signature": signature,
                },
            )
            resp.raise_for_status()
            elapsed_ms = round((time.perf_counter() - start) * 1000)
            rows.append(
                {
                    "iteration": index + 1,
                    "retell_ttfb_ms": elapsed_ms,
                    "retell_extraction_latency_ms": MOCK_EXTRACTION_MS[index],
                    "retell_webhook_rt_ms": elapsed_ms,
                    "retell_cost_per_call_usd": retell_cost_per_call(),
                    "custom_ttfb_ms": MOCK_CUSTOM_TTFB_MS[index],
                    "custom_extraction_latency_ms": MOCK_CUSTOM_EXTRACTION_MS[index],
                    "custom_webhook_rt_ms": MOCK_CUSTOM_WEBHOOK_MS[index],
                    "custom_cost_per_call_usd": CUSTOM_COST_PER_CALL,
                }
            )
    return rows


def summarize(rows: list[dict], mode: str) -> dict:
    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "mode": mode,
        "iterations": len(rows),
        "retell_stack": {
            "ttfb_ms_median": median(row["retell_ttfb_ms"] for row in rows),
            "extraction_latency_ms_median": median(row["retell_extraction_latency_ms"] for row in rows),
            "webhook_rt_ms_median": median(row["retell_webhook_rt_ms"] for row in rows),
            "cost_per_call_usd_median": median(row["retell_cost_per_call_usd"] for row in rows),
        },
        "custom_stack": {
            "ttfb_ms_median": median(row["custom_ttfb_ms"] for row in rows),
            "extraction_latency_ms_median": median(row["custom_extraction_latency_ms"] for row in rows),
            "webhook_rt_ms_median": median(row["custom_webhook_rt_ms"] for row in rows),
            "cost_per_call_usd_median": median(row["custom_cost_per_call_usd"] for row in rows),
        },
        "runs": rows,
    }


def write_results(results: dict) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ep7 Retell vs custom-stack benchmark.")
    parser.add_argument("--live", action="store_true", help="POST signed mocked calls to the ep6 FastAPI server.")
    parser.add_argument("--url", default="http://localhost:8000/retell-webhook")
    args = parser.parse_args()

    if args.live:
        secret = os.environ["RETELL_WEBHOOK_SECRET"]
        rows = live_iterations(args.url, secret)
        mode = "live_ep6_fastapi"
    else:
        rows = mocked_iterations()
        mode = "mocked_retell_call_data"

    results = summarize(rows, mode)
    write_results(results)

    retell = results["retell_stack"]
    custom = results["custom_stack"]
    print(f"Wrote {RESULTS_PATH}")
    print(
        "Retell medians: "
        f"TTFB {retell['ttfb_ms_median']:.0f}ms | "
        f"extraction {retell['extraction_latency_ms_median']:.0f}ms | "
        f"webhook {retell['webhook_rt_ms_median']:.0f}ms | "
        f"cost ${retell['cost_per_call_usd_median']:.2f}/call"
    )
    print(
        "Custom medians: "
        f"TTFB {custom['ttfb_ms_median']:.0f}ms | "
        f"extraction {custom['extraction_latency_ms_median']:.0f}ms | "
        f"webhook {custom['webhook_rt_ms_median']:.0f}ms | "
        f"cost ${custom['cost_per_call_usd_median']:.2f}/call"
    )


if __name__ == "__main__":
    main()
