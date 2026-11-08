"""Lab G - Connect speech input and generated responses to a chatbot.

Goal: build the smallest complete voice assistant: listen, understand, respond, speak.
Every part is local, offline, and free of API keys.

The pipeline::

    microphone file -> recogniser -> intent -> dialogue state -> response text
                                                                      |
                                                          speech synthesiser -> WAV

Three design decisions that matter more than the model:

1. **Intents, not sentences.** A closed command vocabulary means the assistant can map
   "start" to an action. Anything outside the vocabulary is an unknown intent, and
   pretending otherwise is how assistants invent actions.
2. **Confidence gates the dialogue.** Below the floor the assistant asks for a repeat
   instead of acting on a guess. Acting on a 0.4-confidence "stop" is a safety bug.
3. **Responses are template text, then synthesised.** The "generated response" here is
   a deterministic template, not an LLM. Swapping in a language model changes one
   function; it does not change the consent, logging, or error-handling requirements.

There is no microphone in this environment, so the demo synthesises the user's speech
too. Replace ``user_audio`` with ``audio.read_wav("recording.wav")`` and the rest of
the pipeline is unchanged.

Run:

    python lab_g_voice_chatbot.py
    python lab_g_voice_chatbot.py --interactive
    python lab_g_voice_chatbot.py --selftest

Outputs: ``outputs/lab_g_voice_chatbot.json`` and ``outputs/lab_g_turn_*.wav``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from speech_core import asr, audio, datasets, synth, tts

CONFIDENCE_FLOOR = 0.70

RESPONSES = {
    "confirm": "Okay, confirmed.",
    "deny": "Okay, cancelled.",
    "start": "Starting playback.",
    "stop": "Stopped.",
    "previous": "Going back one track.",
    "next": "Skipping to the next track.",
}


class VoiceAssistant:
    """Recognise -> intent -> response -> speech. Small enough to read in one sitting."""

    def __init__(self, recognizer, voice_index: int = 1, confidence_floor: float = CONFIDENCE_FLOOR, max_correction: float = 0.34):
        self.recognizer = recognizer
        self.speaker = tts.FormantTTS(voice_index=voice_index)
        self.confidence_floor = confidence_floor
        # Closed-vocabulary command recognition may snap a near miss to a known word.
        # 0.34 lets "stopt" become "stop" but leaves "stt" and "nestart" alone.
        self.max_correction = max_correction
        self.state = {"playing": False, "track": 0, "awaiting_confirmation": False}

    # -- perception ---------------------------------------------------------
    def transcribe(self, samples: np.ndarray, sample_rate: int = 16_000) -> dict:
        if audio.rms(samples) < 0.004:
            return {"text": "", "confidence": 0.0, "status": "silence"}
        result = self.recognizer.transcribe_samples(samples, sample_rate)
        snapped = asr.lexicon_decode(result["text"], list(datasets.WORDS), max_ratio=self.max_correction)
        status = "ok" if result["confidence"] >= self.confidence_floor and result["text"] else "unsure"
        return {**result, "raw": result["text"], "text": snapped["text"], "corrected": snapped["applied"], "status": status}

    # -- understanding ------------------------------------------------------
    def intent_of(self, text: str) -> str | None:
        word = text.strip().lower()
        return datasets.COMMANDS.get(word)

    # -- acting -------------------------------------------------------------
    def respond(self, intent: str | None) -> str:
        if intent is None:
            return "Sorry, I did not catch a command. You can say yes, no, start, stop, left, or right."
        if intent == "start":
            self.state["playing"] = True
        elif intent == "stop":
            self.state["playing"] = False
        elif intent == "previous":
            self.state["track"] = max(0, self.state["track"] - 1)
            return f"Going back to track {self.state['track'] + 1}."
        elif intent == "next":
            self.state["track"] += 1
            return f"Now on track {self.state['track'] + 1}."
        return RESPONSES[intent]

    # -- one turn -----------------------------------------------------------
    def turn(self, samples: np.ndarray, sample_rate: int = 16_000) -> dict:
        heard = self.transcribe(samples, sample_rate)
        if heard["status"] == "silence":
            reply = "I did not hear anything."
            intent = None
        elif heard["status"] == "unsure":
            reply = "Sorry, could you say that again?"
            intent = None
        else:
            intent = self.intent_of(heard["text"])
            reply = self.respond(intent)
        speech = self.speaker.synthesize(reply)
        return {
            "heard": heard,
            "intent": intent,
            "reply": reply,
            "reply_seconds": round(speech.duration, 3),
            "state": dict(self.state),
            "samples": speech.samples,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interactive", action="store_true", help="type commands as text, as if recognised")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    epochs = 4 if args.selftest else 12
    rec = support.recognizer("base", epochs=epochs, log=False)
    assistant = VoiceAssistant(rec, confidence_floor=CONFIDENCE_FLOOR)

    support.rule("assistant")
    print(f"recogniser  : {rec.as_dict()['parameters_total']:,} parameters")
    print(f"correction  : near misses snapped to the six command words (edit distance <= {assistant.max_correction})")
    print(f"intents     : {', '.join(sorted(datasets.COMMANDS))}")
    print(f"confidence floor: {CONFIDENCE_FLOOR:.2f}; responses are templates, then synthesised")

    support.rule("spoken turns (synthetic user, offline)")
    turns: list[dict] = []
    script = [
        ("start", 0, 0.0),
        ("left", 5, 0.0),
        ("right", 3, 0.0),
        ("stop", 4, 0.0),
        ("banana", 2, 0.0),  # not a command; see the typed turn below
        ("stop", 6, 6.0),  # heavy noise: the assistant should not act on a guess
    ]
    for i, (word, voice_index, snr) in enumerate(script):
        profile = datasets.voice_for(voice_index)
        if word in synth.WORDS:
            samples = synth.speak(word, profile, 16_000)
        else:
            # "banana" cannot be spoken: the phoneme inventory has no /b/. Send silence
            # instead, and exercise the out-of-vocabulary path with a typed turn below.
            samples = np.zeros(16_000, dtype=np.float32)
        if snr > 0:
            samples = audio.add_noise(samples, snr, seed=i)
        result = assistant.turn(samples, 16_000)
        path = audio.write_wav(support.OUT / f"lab_g_turn_{i}.wav", result.pop("samples"), 16_000)
        result["utterance"] = word
        result["audio_in"] = "synthetic"
        result["reply_audio"] = str(path.relative_to(support.HERE))
        turns.append(result)
        heard = result["heard"]
        fixed = f" (from {heard['raw']!r})" if heard.get("corrected") else ""
        print(f"  heard {heard['text']!r:<10} conf {heard['confidence']:.2f} "
              f"({heard['status']:<8}) intent {str(result['intent']):<9} -> {result['reply']}{fixed}")

    if args.interactive:
        support.rule("typed commands (same dialogue logic, no audio)")
        print("Type a command, blank line to finish.")
        while True:
            line = input("> ").strip()
            if not line:
                break
            intent = assistant.intent_of(line)
            reply = assistant.respond(intent)
            speech = assistant.speaker.synthesize(reply)
            turns.append({"heard": {"text": line, "confidence": 1.0, "status": "typed"}, "intent": intent, "reply": reply, "reply_seconds": round(speech.duration, 3)})
            print(f"  {line!r} -> intent {intent} -> {reply}")

    support.rule("out-of-vocabulary text (same dialogue logic, no acoustics)")
    for typed in ("banana", "start"):
        intent = assistant.intent_of(typed)
        reply = assistant.respond(intent)
        turns.append(
            {
                "utterance": typed,
                "audio_in": "typed",
                "heard": {"text": typed, "raw": typed, "confidence": 1.0, "status": "typed", "corrected": False},
                "intent": intent,
                "reply": reply,
            }
        )
        print(f"  typed {typed!r:<10} intent {str(intent):<9} -> {reply}")

    support.rule("dialogue state after the script")
    print(f"  {assistant.state}")

    support.rule("what this assistant cannot do")
    print("  - understand anything outside six command words")
    print("  - answer a question, or hold a conversation about content")
    print("  - recover from a misrecognition without being asked to repeat")
    print("  - transcribe the user's words for a log without a retention policy")

    payload = {
        "lab": "G",
        "title": "voice-enabled chatbot",
        "confidence_floor": CONFIDENCE_FLOOR,
        "model": rec.as_dict(),
        "intents": datasets.COMMANDS,
        "turns": turns,
        "final_state": assistant.state,
        "checks": {},
    }

    expected_playing = False
    for turn in turns:
        if turn["intent"] == "start":
            expected_playing = True
        elif turn["intent"] == "stop":
            expected_playing = False
    typed = [t for t in turns if t["audio_in"] == "typed"]
    checks = {
        "at least one turn produced an intent": any(t["intent"] for t in turns),
        "out-of-vocabulary text produces no intent": all(
            t["intent"] is None for t in typed if t["utterance"] not in datasets.COMMANDS
        ),
        "an intent exists exactly when the text is a command": all(
            (t["intent"] is None) == (t["heard"]["text"] not in datasets.COMMANDS)
            for t in turns
            if t["heard"]["status"] in {"ok", "typed"}
        ),
        "every turn produced a reply": all(t["reply"] for t in turns),
        "state follows only recognised intents": assistant.state["playing"] is expected_playing,
        "a low-confidence turn is never acted on": all(
            t["intent"] is None for t in turns if t["heard"]["confidence"] < CONFIDENCE_FLOOR
        ),
        "every spoken turn produced audio or a clear no-speech message": all(
            t["reply"] for t in turns if t["audio_in"] == "synthetic"
        ),
    }
    failures = 0
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        failures += 0 if passed else 1
    payload["checks"] = checks

    path = support.write_report("lab_g_voice_chatbot.json", payload)
    print(f"\nreport written to {path.relative_to(support.HERE)}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
