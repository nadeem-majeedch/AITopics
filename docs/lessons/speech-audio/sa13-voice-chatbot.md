# SA13 - Building a voice-enabled chatbot {#sa13}

**Section path:** [Overview](index.md) · **Module 13** · [Lab G](labs/lab-g-voice-chatbot.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 1.5 h reading, 2.5 h practice |
| **Hardware** | CPU-only, no microphone required |
| **Prerequisites** | SA07, SA10, SA12 |
| **You will produce** | A working offline voice assistant with a measured dialogue log |

## Why this module exists

Every component so far has been measured in isolation. A voice assistant is the first place
where their errors compound: a recognition error becomes a wrong intent, which becomes a
wrong action, which the user hears as a spoken response that confirms the mistake.

This module builds the smallest complete loop - listen, understand, respond, speak - and
measures it end to end. The interesting design decisions are not in the model; they are in
what the system does when it is unsure.

## The loop

```text
audio -> recogniser -> text -> intent -> dialogue state -> response text -> synthesiser -> audio
          |              |                       |
      confidence     unknown intent        confirmation rules
```

```python
class VoiceAssistant:
    def turn(self, samples, sample_rate=16_000):
        heard = self.transcribe(samples, sample_rate)      # recognise + gate on confidence
        if heard["status"] == "silence":
            reply, intent = "I did not hear anything.", None
        elif heard["status"] == "unsure":
            reply, intent = "Sorry, could you say that again?", None
        else:
            intent = self.intent_of(heard["text"])
            reply = self.respond(intent)
        speech = self.speaker.synthesize(reply)
        return {"heard": heard, "intent": intent, "reply": reply, "speech": speech}
```

The full implementation is `projects/speech-audio/lab_g_voice_chatbot.py`, about 90 lines
including the dialogue state.

## Intents, not sentences

A closed command vocabulary maps words to actions:

```python
from speech_core import datasets

datasets.COMMANDS
# {'yes': 'confirm', 'no': 'deny', 'start': 'start',
#  'stop': 'stop', 'left': 'previous', 'right': 'next'}
```

Anything outside that set is an unknown intent. An assistant that forces every input into
the nearest known action will happily "confirm" a purchase because the user said something
that sounded like "yes". Unknown-intent handling is not a fallback; it is the main safety
control.

```python
def intent_of(self, text):
    return datasets.COMMANDS.get(text.strip().lower())    # None means unknown
```

## Confidence gating

The recogniser returns a confidence. The assistant has three bands:

| Confidence | Behaviour | Why |
| --- | --- | --- |
| < 0.70 | "Sorry, could you say that again?" | acting on a guess is worse than asking |
| blank | "I did not hear anything." | distinct from "I heard something I don't know" |
| >= 0.70 | act, and say what it did | the user must be able to notice a wrong action |

Measured in the lab's scripted dialogue, a noisy "stop" at 6 dB SNR was heard as `sto` with
confidence 0.87 - above the 0.70 floor, and one character from a real command, so lexicon
snapping accepted it and the assistant stopped playback. Runs of this lab before its seeding
was fixed heard the same turn as `so`, which is too far from `stop` to snap (edit distance
ratio 0.5 > 0.34), and asked for a repeat instead. Both behaviours come from the same two
guards - a confidence floor and a distance threshold - and acting instead of asking sat on
which near-miss the model happened to produce.

## Closed-vocabulary correction

Committing a near miss to a known command is legitimate here, and only here:

```python
from speech_core import asr

asr.lexicon_decode("stopt", ["yes", "no", "stop", "start", "left", "right"], max_ratio=0.34)
# {'text': 'stop', 'raw': 'stopt', 'distance': 1, 'ratio': 0.25, 'applied': True}

asr.lexicon_decode("stt", [...], max_ratio=0.34)
# {'text': 'stt', 'ratio': 0.5, 'applied': False}
```

`max_ratio` is a policy decision, not a hyperparameter to tune until the demo looks good.
0.34 fixes a trailing character and leaves genuinely broken input alone. Raise it to 0.5 and
"stt" becomes "stop" - an action taken on two thirds of a word.

## Dialogue state

Even a six-command assistant needs state, and the state must be inspectable:

```python
self.state = {"playing": False, "track": 0, "awaiting_confirmation": False}
```

Two rules that prevent most voice-assistant bugs:

1. **Destructive actions confirm.** "Stop" is recoverable; "delete everything" is not.
2. **A misheard confirmation is not a confirmation.** If confidence is low, ask again rather
   than assuming yes.

## Measured dialogue

Verified run of [Lab G](labs/lab-g-voice-chatbot.md) - synthetic user, offline recogniser:

| User said | Heard | Confidence | Intent | Response |
| --- | --- | --- | --- | --- |
| start | start | 0.97 | start | Starting playback. |
| left | left | 0.88 | previous | Going back to track 1. |
| right | right | 0.98 | next | Now on track 2. |
| stop | stop | 0.95 | stop | Stopped. |
| silence | (nothing) | 0.00 | none | I did not hear anything. |
| stop at 6 dB SNR | sto -> stop | 0.87 | stop | Stopped. |
| typed "banana" | banana | 1.00 | none | Sorry, I did not catch a command... |

Final state: `{'playing': True, 'track': 1}` - the last action was the typed `start`.

Note the noisy row: the assistant acted on a *corrected* word at 0.87 confidence, well above
its floor. That is the design decision this module wants you to argue about. Correction
recovered a true command here; with a worse near-miss the same turn is refused and the user is
asked to repeat. A production assistant should confirm corrected commands below some threshold
instead of acting on them silently, and log the raw text it corrected from.

## Latency budget

A conversational turn feels broken above roughly 1-2 seconds of delay. This pipeline's
components, measured in [Lab H](labs/lab-h-model-comparison.md) and [SA14](sa14-optimization-and-deployment.md):

| Component | Time on this CPU | Note |
| --- | --- | --- |
| recognition, 1.62 s of audio | 6.24 ms | RTF 0.0038, measured over 20 runs |
| intent + templates | microseconds | a dictionary lookup |
| synthesis, 1.62 s of speech | 1.56 ms | formant synthesis generates samples, not predictions |
| end-to-end compute | under 10 ms | dominated by audio capture and endpointing in a real system |

The real latency in a deployed assistant is the *endpointing* delay - how long it waits to
decide you have finished speaking - not the model.

## What this assistant cannot do

* understand anything outside six command words;
* answer a question, or hold a conversation about content;
* recover from a misrecognition without asking the user to repeat;
* transcribe the user's words for a log without a retention policy;
* run on a live microphone in this environment (no audio device), only on files.

That last point is a limitation of the lab machine, not of the design: replace
`user_audio` with `audio.read_wav(path)` and the pipeline is unchanged.

## Adding a language model, safely

Swapping the template responses for an LLM is a one-function change and a dozen new risks:

| Risk | Mitigation |
| --- | --- |
| The model invents an action it cannot perform | constrain output to a validated intent schema |
| Prompt injection through transcribed audio | treat the transcript as untrusted input, never as instructions |
| Personal data sent to a third party | disclose it, minimise it, or keep inference local |
| Cost per turn | rate-limit, cache, and cap output length |
| Hallucinated confirmation | require an explicit tool-call result before saying "done" |

The audio pipeline does not protect you from any of these. Treat the language model as a
component with its own threat model.

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| Every turn asks for a repeat | confidence floor too high, or normalisation mismatch | check `heard["confidence"]` on clean audio |
| Wrong command executed at low confidence | no confidence gate | gate before intent mapping |
| "banana" triggers an action | nearest-word snapping too permissive | lower `max_ratio`, check the raw text |
| State drifts from what the user hears | action applied but response text stale | build the response from state after the action |
| Response audio is silent | synthesiser spelled an out-of-vocabulary reply | check `SynthesisResult.note` |

## Exercises

1. Add a seventh intent ("louder") and a response, then measure whether the recogniser can
   produce it at all. What does that tell you about expanding a voice interface?
2. Remove the confidence gate and re-run the noisy turn. Which action does the assistant
   take, and how would a user notice?
3. Add a confirmation step for "stop" and measure how many extra turns it costs in the
   scripted dialogue.
4. Write the retention policy for the transcript log this assistant would keep, in five
   sentences.

Next: [SA14 - Inference optimization, evaluation, and responsible deployment](sa14-optimization-and-deployment.md)
