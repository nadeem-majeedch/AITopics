# Lab G - Connect speech input and generated responses to a chatbot

**Section path:** [Overview](../index.md) · Module [SA13](../sa13-voice-chatbot.md) · **Lab G** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only; no microphone needed |
| **Code** | `projects/speech-audio/lab_g_voice_chatbot.py` |
| **Prerequisite** | SA07, SA10, SA13 |

## The task

Build the complete loop - listen, understand, respond, speak - and show what it does when it
is unsure. Every turn writes the recognised audio, the reply audio, and the dialogue state,
so the failure cases are auditable.

You must produce:

1. a spoken turn table with the heard text, confidence, intent, and reply;
2. the reply audio files, one per turn;
3. the final dialogue state;
4. the out-of-vocabulary case and the noisy case, both handled without acting.

## Run it

```bash
cd projects/speech-audio
python lab_g_voice_chatbot.py
python lab_g_voice_chatbot.py --interactive   # type commands, same dialogue logic
python lab_g_voice_chatbot.py --selftest
```

```text
=== spoken turns (synthetic user, offline)
  heard 'start'    conf 0.97 (ok      ) intent start     -> Starting playback.
  heard 'left'     conf 0.88 (ok      ) intent previous  -> Going back to track 1.
  heard 'right'    conf 0.98 (ok      ) intent next      -> Now on track 2.
  heard 'stop'     conf 0.95 (ok      ) intent stop      -> Stopped.
  heard ''         conf 0.00 (silence ) intent None      -> I did not hear anything.
  heard 'stop'     conf 0.87 (ok      ) intent stop      -> Stopped. (from 'sto')

=== out-of-vocabulary text (same dialogue logic, no acoustics)
  typed 'banana'   intent None      -> Sorry, I did not catch a command...
  typed 'start'    intent start     -> Starting playback.

=== dialogue state after the script
  {'playing': True, 'track': 1, 'awaiting_confirmation': False}
```

## What each turn demonstrates

| Turn | Demonstrates |
| --- | --- |
| `start` | the happy path: recognise, map, act, speak |
| `left` / `right` | state changes are reflected in the response ("track 1", "track 2") |
| `stop` | clean command, no correction needed |
| silence | no speech is a distinct outcome from "not understood" |
| `stop` at 6 dB, heard as `sto` | correction saved a true command - and acted on it at 0.87 |
| typed `banana` | out-of-vocabulary text is never forced into an intent |

The noisy row is the interesting one, and it cuts both ways. Here snapping turned `sto` into
`stop`: a real command the user wanted, recovered from 6 dB of noise. A worse near-miss - `so`,
say - is too far from `stop` to snap and gets a request to repeat instead. So the interface's
correctness on this turn depends on which near-miss the model produced, which is why acting on
a corrected command at 0.87 confidence deserves either a confirmation step or an audit log in a
real product. The lab's checks assert the *logic* (an intent exists exactly when the text is a
command, a low-confidence turn is never acted on, every turn gets a reply), not an exact
transcript.

## Checks

```text
PASS  at least one turn produced an intent
PASS  out-of-vocabulary text produces no intent
PASS  an intent exists exactly when the text is a command
PASS  every turn produced a reply
PASS  state follows only recognised intents
PASS  a low-confidence turn is never acted on
PASS  every spoken turn produced audio or a clear no-speech message
```

## Reply audio

Every reply is synthesised and written next to the report:

```text
outputs/lab_g_turn_0.wav   1.62 s   "Starting playback."
outputs/lab_g_turn_3.wav   0.55 s   "Stopped."
outputs/lab_g_turn_4.wav   0.85 s   "I did not hear anything."
```

The durations are measured, not estimated. The synthesiser is a formant model, so the replies
sound robotic; that is expected and is not a bug in your pipeline.

## The safety decisions in the code

| Decision | Where | Why |
| --- | --- | --- |
| Confidence floor 0.70 | `VoiceAssistant.transcribe` | act only on confident recognition |
| Correction ratio 0.34 | `lexicon_decode` | fix a trailing character, not half a word |
| Unknown intent returns `None` | `intent_of` | never invent an action |
| State read after the action | `respond` | the spoken reply matches reality |

Any one of these removed turns the assistant into something that acts on guesses.

## Write-up requirements

1. The turn table with all six columns.
2. One paragraph on why `so` was not corrected to `stop`, and what would happen if the
   correction floor were raised until it was.
3. The final dialogue state and how the script produced it.
4. Two sentences on what you would need to change to run this on a live microphone.

## Independent extensions

* Add a "louder" intent and a response, and see whether the recogniser can produce it at all.
* Raise the correction ratio to 0.5 and re-run the noisy turn: which action is taken?
* Add a confirmation step for "stop" and count the extra turns it costs.
* Replace the template responses with a small language model call and list three new failure
  modes you would have to test.

Next: [Lab H - Compare inference speed and recognition quality](lab-h-model-comparison.md)
