# Governance statement - Video AI {#governance}

**Section path:** [Overview](index.md) · [Responsible use](vd15-responsible-video-analytics.md) · **Governance** · [Model card](model-card.md)

A template with the section's own answers filled in. Copy it into your capstone and replace every
value. If a line cannot be answered, that is the finding: the system is not ready to be deployed.

## 1. Purpose

| Question | This section | Your project |
| --- | --- | --- |
| What decision does the system support? | Teaching: demonstrate detection, tracking, counting, and evaluation on synthetic traffic footage | |
| Who is the intended user? | A student or developer running the labs locally | |
| What is explicitly out of scope? | Identifying people, inferring protected attributes, cross-camera re-identification, enforcement decisions | |

## 2. Legal basis and jurisdiction

| Question | This section | Your project |
| --- | --- | --- |
| Where does the data come from, and under what right? | Synthetic generation, CC0-1.0; no personal data is processed | |
| Is personal data processed? | No: rectangles on a rendered road, no faces, no plates, no location | |
| Which regime applies? | None for the synthetic data; a real deployment in the EU/UK would engage GDPR (Art. 6 basis, Art. 9 for special categories), plus sector rules | |
| Has a data protection impact assessment been done? | Not applicable here; **required** before any deployment on real footage | |

Note for real footage: a DPIA is not paperwork you do after building. It frequently changes the
design - retention, aggregation, on-device processing, or not collecting at all.

## 3. Data

| Question | This section | Your project |
| --- | --- | --- |
| Source | `scripts/make_video_data.py`, deterministic, seed 0 | |
| Content | 7 clips x 60 frames, 640x360, 10 fps, 4 vehicle classes | |
| Personal data | none | |
| Licence | CC0-1.0 | |
| Retention | regenerable in ~2 s; `data/video/` is git-ignored and safe to delete | |
| Access | local machine, repository permissions | |

## 4. Model and system

| Question | This section | Your project |
| --- | --- | --- |
| Components | `TinyDetector` (138,579 params, scratch), `SSDLiteDetector` (3.44 M, COCO, baseline), `IoUTracker`, `LineCounter`, `GarmentNet` (24,458), `TemporalClassifier` (48,805) | |
| Outputs | boxes, classes, track IDs, counts, aggregate flow, review video | |
| Outputs deliberately absent | identity, face, plate, gender, age, ethnicity, health | |
| Where it runs | local CPU, one torch thread | |
| Artefacts | reports in `outputs/`, video only for review | |

## 5. Measured limitations

| Limitation | Measurement | Consequence |
| --- | --- | --- |
| Night footage is effectively undetected | fine-tuned mAP 0.033, recall 0.044 | do not deploy at night without new data |
| Congested scenes undercount | 5 of 8 vehicles, MOTA -0.381 | do not use for dense junctions |
| Camera shake breaks counting | 3 of 6 counted, MOTA -0.019 | stabilise, or do not use a moving mount |
| Colour attributes fail in low light | 1.000 → 0.133 at 0.45 brightness | colour needs correction, not a bigger model |
| Identity fragments under occlusion | 14 tracks for 6 vehicles | per-track aggregates, not per-vehicle claims |

These are not caveats appended to a success story; they are the section's results.

## 6. Access, retention, and deletion

| Question | This section | Your project |
| --- | --- | --- |
| Who can run it? | anyone with the repository | |
| Who can see outputs? | the person who ran it | |
| What is retained after a run? | JSON summaries and a review video in `outputs/` | |
| Deletion | delete `outputs/` and `data/video/`; both are regenerable | |
| Logs | Lab 7 writes a summary per run, including input, stride, and counts | |

For real footage, add: where recordings are stored, who holds the key, how long raw video is
kept, and how a deletion request is honoured.

## 7. Accountability

| Question | This section | Your project |
| --- | --- | --- |
| Who owns the system? | the course maintainers | |
| Who reviews changes? | code review before merge | |
| How is a problem reported? | an issue in the repository | |
| What happens when the system is wrong in public? | the report states the failure rate; the system is not deployed | |

## 8. Review

| Trigger | Action |
| --- | --- |
| New footage source | new data card, new legal basis check, re-run the split audit |
| New output field | re-read this page; a new field is a scope change, not a feature |
| Accuracy regression | re-measure on the held-out videos; do not tune on test |
| Incident | stop, document, fix, and record the fix |

## Sign-off

| Role | Name | Date |
| --- | --- | --- |
| Author | | |
| Reviewer | | |
| Data owner (if real footage) | | |

An unsigned governance statement is an unfinished section, not a formality. If nobody will put
their name to it, the deployment has no accountable owner - and that, by itself, is the reason
not to ship.
