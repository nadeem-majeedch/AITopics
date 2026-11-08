# Lab 2 - Dataset audit, split probe, and card {#lab-2}

**Section:** [Model training](../index.md) · **Modules:** M05 · **Time:** 7 hours

## Goal

Audit a dataset you intend to use, clean it with a documented rule, prove your
split does not leak, and publish a card that reconciles with the raw file.

You may use the ticket data or a dataset from your own project. The lab is marked
on the audit and the evidence, not on the dataset's size.

## Steps

1. **Audit the raw file.** Report rows, columns, dtypes, blanks, exact duplicate
   texts, duplicate texts with conflicting labels, label values and counts, text
   length quantiles, and a digest.
2. **Write the cleaning rule.** Normalise labels with an explicit map that raises
   on unknown values. Drop blank text and exact duplicate text. Log every dropped
   row with a reason.
3. **Prove reconciliation.** Show that raw - dropped = clean, and that the class
   counts in the card match the cleaned file.
4. **Split twice.** Random rows and grouped by entity. For each, report the number
   of test rows whose exact text appears in training and the accuracy of the same
   classifier.
5. **Measure near-duplicates.** Choose a similarity threshold, report the pair
   count and two examples, and explain whether the count reflects defects or
   templates.
6. **Generate a card.** Include a digest, composition, preprocessing, intended and
   out-of-scope uses, and one limitation about a group that is not represented.

## Deliverables

| File | Contents |
| --- | --- |
| `audit.json` | Machine-readable counts for both raw and clean files |
| `clean.py` | Cleaning function with tests for row counts and unknown labels |
| `split_report.md` | Random vs grouped table, overlap probe, accuracy |
| `dataset_card.md` | Generated card with digest |
| `report.md` | Decisions, rejected alternatives, limitations |

## Marking

* **30%** audit is complete and reconciles with the cleaned file.
* **25%** cleaning is deterministic, logged, and tested.
* **20%** split probe is present for both strategies and interpreted correctly.
* **15%** card has all sections and a digest, and claims trace to counts.
* **10%** limitations name a missing group and an out-of-scope use.

## Failure cases the marker will try

* A file with a new label spelling: does your cleaner fail loudly?
* A file with a duplicate text and conflicting labels: is it flagged, not averaged?
* A test row that is an exact duplicate of a train row: does the probe count it?

## Rules

Keep the raw file untouched. Do not hand-edit the card after generation; change
the statistics or the template and regenerate it.
