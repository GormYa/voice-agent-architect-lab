# EP7 Platform Comparison

Benchmark and database-inspection helpers for the Retell platform versus custom
stack comparison.

## Benchmark

The default run uses deterministic mocked Retell call data so the output matches
the slide numbers:

```powershell
cd ep7-platform-comparison
python benchmark.py
```

To hit a running ep6 backend instead:

```powershell
$env:RETELL_WEBHOOK_SECRET="your_retell_webhook_secret_here"
python benchmark.py --live --url http://localhost:8000/retell-webhook
```

Both modes write `results/benchmark_results.json`.

## Query Leads

After an ep6 call or live benchmark run:

```powershell
python query_leads.py
```

The script reads `..\ep6-retell-custom-backend\leads.db` and prints the last ten
leads in a narrow terminal-friendly table.
