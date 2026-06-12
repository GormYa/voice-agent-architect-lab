#!/usr/bin/env bash
sqlite3 leads.db "SELECT call_id, qualified, json_extract(variables, '$.budget') AS budget FROM leads ORDER BY created DESC LIMIT 3;"
