from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import time

sys.path.append(str(Path(__file__).resolve().parents[1]))

from graph.barge_in import (
    AudioWindow,
    BargeInDetected,
    handle_user_audio_event,
    perform_barge_in_rollback,
)
from graph.supervisor import build_graph
from state.redis_checkpointer import RedisCheckpointer
from state.voice_state import VoiceState


@dataclass
class FakeTTSPlayer:
    speaking: bool = False
    cancelled: list[str] | None = None
    audible: bool = True

    def start(self):
        self.speaking = True

    def speak(self, text: str):
        if not self.audible:
            print(f"[audio-off] {text}")
            return
        self._speak_windows(text)

    def stop(self):
        self.speaking = False
        print("[rollback-1] stop TTS: stream halted")

    def cancel(self, tts_id: str):
        if self.cancelled is None:
            self.cancelled = []
        self.cancelled.append(tts_id)
        print(f"[cancel] cancelled in-flight TTS chunk: {tts_id}")

    @staticmethod
    def _speak_windows(text: str) -> None:
        escaped = text.replace("'", "''")
        command = (
            "Add-Type -AssemblyName System.Speech; "
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$synth.Speak('" + escaped + "')"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=False,
            capture_output=True,
            text=True,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EP4 barge-in live demo")
    parser.add_argument("--interrupt-ms", type=int, default=1800)
    parser.add_argument("--energy", type=float, default=0.9)
    parser.add_argument("--no-pause", action="store_true")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0")
    parser.add_argument("--thread-id", default="voice-thread")
    parser.add_argument("--checkpoint-id", default="turn-21")
    parser.add_argument("--silent-audio", action="store_true")
    return parser.parse_args()


def maybe_pause(args: argparse.Namespace, message: str) -> None:
    if args.no_pause:
        print(message)
        return
    input(message)


def main() -> int:
    args = parse_args()
    thread_id = args.thread_id
    checkpoint_id = args.checkpoint_id
    cp = RedisCheckpointer.from_url(args.redis_url, ttl_seconds=600)
    graph = build_graph(checkpointer=cp)
    tts = FakeTTSPlayer(audible=not args.silent_audio)

    # Initial long response setup
    base_state: VoiceState = {
        "current_utterance": "Tell me a long explanation about museum voice orchestration.",
        "turn_history": [],
        "active_task": None,
        "checkpoint_id": checkpoint_id,
        "in_flight_tts": ["chunk-1", "chunk-2"],
    }
    cp.put(thread_id, checkpoint_id, base_state)
    print(f"[redis] seeded checkpoint with HSET key=voice_state:{thread_id} field={checkpoint_id}")

    tts_window = AudioWindow(tts_start_ms=1000, tts_end_ms=4200)
    agent_lines = [
        "Agent: In this architecture, the supervisor routes requests by intent.",
        "Agent: We checkpoint state before each major generation step.",
        "Agent: That way, interruptions can resume from a known point.",
    ]

    maybe_pause(args, "[demo] Press Enter to start agent audio...")
    print("[audio] agent begins multi-sentence response")
    tts.start()

    start = time.perf_counter()
    interrupted = False
    for idx, line in enumerate(agent_lines):
        elapsed_ms = int((time.perf_counter() - start) * 1000) + tts_window.tts_start_ms
        print(f"[tts @ {elapsed_ms}ms] {line}")
        tts.speak(line.replace("Agent: ", ""))
        if idx == 1:
            try:
                print(f"[event] user_audio timestamp={args.interrupt_ms}ms energy={args.energy}")
                handle_user_audio_event(
                    user_audio_timestamp_ms=args.interrupt_ms,
                    tts_window=tts_window,
                    user_audio_energy=args.energy,
                )
            except BargeInDetected as exc:
                interrupted = True
                print(f"[event] BargeInDetected: {exc}")
                rolled_state = perform_barge_in_rollback(
                    tts_controller=tts,
                    redis_checkpointer=cp,
                    thread_id=thread_id,
                    checkpoint_id=checkpoint_id,
                    current_state=base_state,
                    interruption_utterance="Stop. Just summarize the key point in one sentence.",
                )
                print("[rollback-2] get checkpoint: HGET + JSON deserialization complete")
                print("[rollback-3] inject interruption context: current_utterance replaced")
                resumed = graph.invoke(rolled_state)
                print("[resume] agent interruption response:")
                print(resumed["agent_response"])
                tts.speak(resumed["agent_response"])
                break
        time.sleep(0.8)

    if not interrupted:
        tts.stop()
        print("[demo] no interruption was detected; increase energy or adjust interrupt-ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
