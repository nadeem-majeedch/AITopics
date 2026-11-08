"""Hands-on face exercises: detection, landmarks, verification, identification.

Every image is synthetic. The exercises are:

1. **Detection** - recall overall and per tone group. The colour rule is classic
   and its failure is measured, not asserted.
2. **Landmarks** - eye and mouth positions, with the median pixel error against
   the ground truth.
3. **Verification** - is this pair the same person? FAR/FRR and the equal error
   rate, because accuracy hides which error you are making.
4. **Identification** - 1:N search. Rank-1 accuracy, and what happens to an
   unenrolled person when there is no rejection threshold.

Scope: no video, no tracking, no persistent gallery, no real person. If you point
this at photographs of people you need their consent and a lawful basis; the code
cannot give you either.

Run:

    python project_faces.py
    python project_faces.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vision_core import faces, metrics

OUTPUTS = Path(__file__).resolve().parent / "outputs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    records = faces.make_face_dataset(per_identity=8, seed=4)
    print(f"images {len(records)}  identities {len({r.identity for r in records})}  size {records[0].image.shape}")

    # 1. detection ---------------------------------------------------------
    detection = faces.detection_report(records)
    print(f"\n=== detection (IoU >= {detection['iou_threshold']})")
    print(f"overall recall {detection['overall_recall']:.3f} on {detection['n']} images")
    for group, stats in sorted(detection["per_group"].items()):
        print(f"  {group:<16} recall {stats['recall']:.3f}  ({stats['hits']}/{stats['n']})")
    print("this gap is a property of the colour rule, not of the people; it is why")
    print("production systems use learned detectors and still audit per-group recall")

    # 2. landmarks ---------------------------------------------------------
    errors = []
    for rec in records:
        found = faces.detect_face(rec.image)
        box = found["box"] if found["found"] else rec.truth_box
        landmarks = faces.locate_landmarks(rec.image, box)
        if landmarks.get("found"):
            error = faces.landmark_error(landmarks, rec.landmarks)
            if not np.isnan(error):
                errors.append(error)
    median_error = float(np.median(errors)) if errors else float("nan")
    print(f"\n=== landmarks\nlocalized on {len(errors)}/{len(records)} faces; median error {median_error:.2f} px")

    # 3. verification ------------------------------------------------------
    scores, same = faces.pair_scores(records)
    eer = metrics.equal_error_rate(scores, same)
    print(f"\n=== verification ({len(scores)} pairs, {sum(same)} same-identity)")
    for threshold in (0.9, 0.95, 0.98):
        row = metrics.verification_metrics(scores, same, threshold)
        print(f"  threshold {threshold:.2f}: FAR {row['far']:.3f}  FRR {row['frr']:.3f}  accuracy {row['accuracy']:.3f}")
    print(f"  equal error rate {eer['eer']:.3f} at threshold {eer['threshold']:.3f}")

    # 4. identification ----------------------------------------------------
    gallery_records = [r for r in records if r.meta["variant"] < 6]
    probe_records = [r for r in records if r.meta["variant"] >= 6]
    gallery = faces.enroll(gallery_records, consent_note="synthetic identities, generated for this exercise")

    gallery_vectors, gallery_labels = gallery["embeddings"], gallery["labels"]
    correct = 0
    for probe in probe_records:
        vector, _ = faces.embed_face_records([probe])
        sims = gallery_vectors @ vector[0]
        best = int(np.argmax(sims))
        correct += int(gallery_labels[best] == probe.identity)
    rank1 = correct / max(1, len(probe_records))
    print(f"\n=== identification\nrank-1 {rank1:.3f} on {len(probe_records)} probes against {len(gallery_records)} enrolled images")

    impostor = faces.FaceIdentity("id_stranger", (140, 95, 70), "tone_a", 0.72, 0.42, 0.30, 0.34, 0.05)
    strangers = faces.make_face_dataset([impostor], per_identity=4, seed=9)
    stranger_matches = 0
    for rec in strangers:
        vector, _ = faces.embed_face_records([rec])
        if float(np.max(gallery_vectors @ vector[0])) >= 0.5:
            stranger_matches += 1
    print(f"unenrolled people matched anyway at threshold 0.5: {stranger_matches}/{len(strangers)}")
    print("identification without a rejection threshold always returns someone; that is the risk")
    print("a 1:N system carries and a 1:1 check does not")

    failures = 0
    if len(detection["per_group"]) < 4:
        print("FAIL  expected at least four tone groups")
        failures += 1
    if not 0.0 <= eer["eer"] <= 1.0:
        print("FAIL  EER outside 0-1")
        failures += 1
    if rank1 < 0.5:
        print(f"FAIL  rank-1 {rank1:.3f} below the 0.5 floor")
        failures += 1
    if not errors:
        print("FAIL  landmarks were never localized")
        failures += 1

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS / "faces_report.json"
    path.write_text(
        json.dumps(
            {
                "detection": detection,
                "landmark_median_error_px": median_error,
                "verification": {
                    "n_pairs": len(scores),
                    "n_same": int(sum(same)),
                    "eer": eer,
                    "at_0.95": metrics.verification_metrics(scores, same, 0.95),
                },
                "identification": {"rank1": rank1, "n_probes": len(probe_records), "gallery": len(gallery_records)},
                "impostor_matched_without_rejection": stranger_matches,
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\nreport: {path}")

    print(f"\n{failures} failure(s)")
    if failures == 0:
        print("PASS  detection, landmarks, verification, and identification all measured")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
