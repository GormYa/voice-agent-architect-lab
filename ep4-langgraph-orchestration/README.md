# EP4 LangGraph Orchestration

Stateful turn orchestration, interruption handling, speculative response, and semantic caching.

## Slide 4 demo

Show these files in order:

1. `state\voice_state.py` - `VoiceState` with `current_utterance`, `turn_history`, `active_task`, and `checkpoint_id`.
2. `graph\supervisor.py` - `Supervisor.invoke`, `classify_intent`, and `route_after_supervisor`.
3. `graph\supervisor.py` - `build_graph`, including `add_node`, `add_conditional_edges`, and `add_edge`.

Run the demo from the repo root:

```powershell
python ep4-langgraph-orchestration\graph\supervisor.py
```

The output shows a booking utterance routed through the Supervisor node into the
booking sub-agent with updated `turn_history`, `active_task`, `intent`, and
`agent_response`.

Implementation note: LangGraph reserves `checkpoint_id` internally, so the public
slide-facing `VoiceState` uses `checkpoint_id`, while the compiled LangGraph
runtime maps that field to `checkpoint_ref` inside the graph.

## Redis checkpoint + barge-in demo cue

Show these sections:

1. `state\redis_checkpointer.py`
`RedisCheckpointer._put_state` shows Redis `HSET` + `EXPIRE` (TTL) with JSON serialization.
`RedisCheckpointer._get_state` shows Redis `HGET` + JSON deserialization.
2. `graph\supervisor.py`
`build_graph(checkpointer=...)` compiles with `graph.compile(checkpointer=checkpointer)`.
3. `graph\barge_in.py`
`resume_from_redis_checkpoint(...)` reads checkpointed state and resumes graph execution.

Quick local proof without a live Redis server:

```powershell
pytest -q ep4-langgraph-orchestration\tests\test_redis_checkpointer.py
```

## Barge-in live demo cue

Show these sections:

1. `graph\barge_in.py`
`handle_user_audio_event(...)` performs timestamp overlap detection and raises `BargeInDetected`.
2. `graph\barge_in.py`
`perform_barge_in_rollback(...)` implements the three-step rollback:
`stop TTS` -> `get checkpoint` -> `inject interruption context`.
3. `graph\barge_in.py`
`resume_from_redis_checkpoint(...)` shows checkpoint read + graph resume.

Run:

```powershell
python ep4-langgraph-orchestration\demo\barge_in_live_demo.py --no-pause
```

This demo prints the full interruption flow and resumes the supervisor graph with
the interruption utterance.

## Speculative TTS + cancellation demo cue

Show these sections:

1. `graph\speculative.py`
`stream_tokens_with_boundaries(...)` shows the token accumulation loop, sentence
boundary regex check, and boundary-triggered TTS dispatch.
2. `state\voice_state.py`
`in_flight_tts` tracks active speculative TTS chunk IDs.
3. `graph\barge_in.py`
`perform_barge_in_rollback(...)` cancels `in_flight_tts` IDs during rollback.

Run latency comparison:

```powershell
python ep4-langgraph-orchestration\demo\speculative_latency_demo.py
```

Run interruption + cancellation flow:

```powershell
python ep4-langgraph-orchestration\demo\barge_in_live_demo.py --no-pause
```

The first command gives measurable full-response vs speculative first-audio timing,
and the second command shows cancellation of in-flight chunks during barge-in.

## Semantic cache demo cue

Show these sections:

1. `graph\semantic_cache.py`
`SemanticCache.check_cache(...)` shows embedding generation, cosine similarity
comparison across stored entries, threshold check, and cache-hit return path.
2. `graph\semantic_cache.py`
`store_response(...)` and `FakeRedisHash` show the Redis hash structure:
normalized question key -> JSON payload containing `embedding` + cached `response`.

Run:

```powershell
python ep4-langgraph-orchestration\demo\semantic_cache_live_demo.py
```

The demo asks the same question with three phrasings and prints cache miss/hit
status, similarity score, and latency per query.

## Slide 9 terminal recording setup (climax demo)

Terminal pane 1 (run the demo with audible speech + real Redis):

```powershell
python ep4-langgraph-orchestration\demo\barge_in_live_demo.py --no-pause --redis-url redis://localhost:6379/0
```

Terminal pane 2 (watch live Redis commands):

```powershell
redis-cli MONITOR
```

Expected in pane 2 during the run:

1. `HSET voice_state:voice-thread turn-21 ...`
2. `EXPIRE voice_state:voice-thread 600`
3. `HGET voice_state:voice-thread turn-21`

If Redis is not running locally, start one (Docker):

```powershell
docker run --name ep4-redis -p 6379:6379 -d redis:7
```
