# F12 lab - Diagnose a training curve before trusting the model

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F12 module score |
| **Time** | About 3 hours |
| **Hardware** | CPU is sufficient; a GPU changes speed only |
| **Starter file** | `labs/foundations/f12_training_curves.md` |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |
| **Data** | `datasets/foundations/generated/student_performance.csv` |

## The scenario

A tutoring program ran a 150-student pilot and recorded study hours, attendance,
prior score, sleep hours, tutoring status, and course, plus whether each student
passed. The program wants a small neural network that flags students who may need
support.

You are the reviewer. You are not asked to maximize accuracy. You are asked to
train a model on the pilot data, **diagnose whether it is underfitting or
overfitting**, apply two controlled changes, and recommend one configuration with
an early-stopping rule that another person could reproduce.

The dataset is synthetic and comes from this repository. Read the
[dataset card](../../technical/foundation-assets.md#foundation-datasets) and the
[generator](../../technical/foundation-assets.md#data-generator) before you start. Generated
tables are not committed, so run the generator once if
`datasets/foundations/generated/` is empty:

```powershell
python scripts/make_foundation_data.py
```

!!! warning "Not a decision tool"
    The student table is synthetic and is not a measurement of any real course.
    Your model must not be used to make decisions about people. The lab is about
    reading curves, not about predicting real students.

## What you must decide

Choose one configuration and one stopping rule, supported by validation curves,
and state what you would do before using it on real data. "Train longer" is not a
diagnosis.

Requirements:

- at least **two controlled changes**, each altering one factor;
- a **diagnosis** of under- or overfitting with numbers and epoch references;
- a **final test evaluation** done once, after the configuration is frozen;
- three seeds for the final configuration, reported as mean and spread.

## Required steps

### Step 1 - Audit the table and define the target

Load the CSV. Confirm 500 rows, the columns listed above, and the pass rate. The
target is `passed`.

**Exclude `final_score` from the features.** It is recorded after the course and
is derived from the same assessment as the target; using it is target leakage and
will inflate accuracy toward 1.00. If you want to demonstrate the leak, train one
throwaway model with it and report the gap, but never include it in your final
model.

Encode `tutoring` as 0/1 and one-hot encode `course` with one column dropped.

**Validation check 1:** print the feature matrix shape and its column names. The
shape must be `(500, k)` with no `final_score`, and `k` must equal the number of
columns you can name individually. A shape you cannot explain is a bug.

### Step 2 - Split, then simulate the pilot

Split 60/20/20 with `train_test_split(..., stratify=y, random_state=42)` to get
300 training, 100 validation, and 100 test rows.

Then take a fixed random subset of **150 rows from the training split only** and
use that as your pilot training set. Leave validation and test untouched. Record
the row indices you selected so the subset is reproducible.

Why: small training sets make the overfitting signal visible. This is the
condition the program is actually in after a pilot.

### Step 3 - Scale correctly

Fit `StandardScaler` on the 150 pilot rows only. Transform validation, test, and
any later data with those statistics.

**Validation check 2:** the standardized pilot features have mean near 0 and
standard deviation near 1. The validation set's mean will not be 0, and that is
correct.

### Step 4 - Establish a baseline

Train logistic regression on the same 150 rows and record validation accuracy.
This is the number your network must beat to justify its complexity.

### Step 5 - Train the first network and record curves

Build a small PyTorch model, for example `Linear(k, 16) -> ReLU -> Linear(16, 16)
-> ReLU -> Linear(16, 1)`, with `BCEWithLogitsLoss`, Adam, learning rate `0.01`,
and full-batch training for 300 epochs. With `k = 7` this model has 417
parameters; compute the exact count for your own `k`.

Every 5 epochs, record training loss, validation loss, training accuracy, and
validation accuracy. Plot the loss and accuracy curves side by side.

**Validation check 3:** rerun the first 20 epochs with the same seed and confirm
the losses match to four decimal places. If they do not, seeding or data order is
uncontrolled.

### Step 6 - Diagnose before changing anything

Write a short diagnosis with evidence:

- the epoch where validation loss is lowest;
- the train-validation loss gap at that epoch and at the final epoch;
- whether both losses are high (underfitting), or training loss is much lower
  than validation loss (overfitting);
- whether accuracy and loss tell the same story.

Do not adjust hyperparameters until this paragraph exists.

### Step 7 - Controlled change 1: capacity

Change **only** the architecture, for example `(16, 16)` to `(64, 64)` or to
`(4,)`. Keep data, seed, optimizer, learning rate, and epochs fixed. Record the
new parameter count and the same curve statistics.

State whether the change reduced the gap, increased it, or did nothing, and
whether the diagnosis supports more or less capacity.

### Step 8 - Controlled change 2: regularization or early stopping

Choose one:

- **Weight decay:** add `weight_decay=1e-2` to Adam, everything else fixed.
- **Early stopping:** keep the architecture and stop at the epoch with the lowest
  validation loss; report that epoch and the corresponding weights.

If you use early stopping, explain how you avoid tuning the stopping epoch on the
test set. Validation only.

Optionally repeat the final recipe with three seeds and report mean and standard
deviation of validation and test accuracy.

### Step 9 - Freeze and evaluate once

Choose the configuration using validation evidence. Then evaluate on the test set
exactly once and report accuracy, precision, recall, F1, and the confusion matrix
for the positive class (`passed = 1`). Explain which error type matters more to a
tutoring program and why.

### Step 10 - Package the evidence

Write a JSON Lines log with one record per run: run name, seed, architecture,
learning rate, weight decay, epochs, best epoch, best validation loss, final
train loss, final validation loss, test metrics, device, and runtime. Write the
report described below.

## Deliverables

```text
f12-curves-lab/
  README.md               # rerun instructions, 5-10 lines
  train_curves.ipynb      # or .py, executed end to end
  runs.jsonl              # one record per run
  curves_baseline.png     # first model, train and validation
  curves_changed.png      # after both controlled changes
  results.csv             # per-run metrics
  report.md               # follows the template below
  reflection.md           # 200-300 words
```

## Report template

```markdown
# F12 training-curve diagnosis

## 1. Question and decision
The stopping rule and configuration you recommend.

## 2. Data and split
Rows, features, excluded columns, pilot subset, class balance.

## 3. Method
Model, loss, optimizer, learning rate, epochs, seeds, device.

## 4. Baseline
Logistic regression result on the same pilot rows.

## 5. Curves and diagnosis
Best epoch, gaps, under- or overfitting, accuracy versus loss.

## 6. Controlled changes
Change 1 and change 2, each with one factor altered and the effect measured.

## 7. Final evaluation
Test metrics and confusion matrix, computed once.

## 8. Reproduction
Commands, versions, hardware, runtime, seeds.

## 9. Ethics and limits
Why this model must not be used for real student decisions; what data would be
needed before any deployment discussion.
```

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | Split, subset, scaling, leakage exclusion, and training loop are correct; metrics match the log | Model trains but leakage remains, or scaling uses validation data |
| Evaluation and diagnosis | 25 | Diagnosis cites epochs and gaps; both changes isolate one factor; final test used once | Curves plotted but not interpreted; changes confounded |
| Reproducibility | 15 | Seeds, subset indices, versions, commands, and hardware reproduce every row | Partial seeds or missing run details |
| Data and ethics | 15 | Leakage handled, provenance cited, no claims about real students, limitations explicit | Leakage unaddressed or the report implies deployability |
| Communication | 15 | Clear curves, tables, and a decision a reviewer can follow | Disorganized or missing the decision |

A dimension without evidence scores zero.

## Privacy and safety constraints

- Use only the synthetic table in this repository. Do not substitute real student
  records.
- Do not include names, student IDs, emails, or institutional data in any file.
- The model is a teaching artifact. Do not present it as a screening tool or use
  it to make decisions about people.
- Redact absolute paths, usernames, and hostnames from logs and screenshots.
- Report measured runtime and device; do not estimate a GPU time you did not run.

## Self-check before submission

- [ ] `final_score` is absent from the feature matrix and I can name every column.
- [ ] The pilot subset is 150 rows drawn only from the training split, with
      recorded indices.
- [ ] The scaler was fitted on pilot rows only.
- [ ] I recorded curves every 5 epochs and can name the best epoch.
- [ ] My diagnosis names under- or overfitting with numbers.
- [ ] Each controlled change altered exactly one factor.
- [ ] The test set was evaluated once, after freezing the configuration.
- [ ] I report three seeds for the final recipe, or explain why not.
- [ ] Ethical limits are stated explicitly.
- [ ] No personal paths remain in the submission.

Next: score the work with the [assessment](assessment.md), then continue to
[F13 - Reproducibility](../f13-reproducibility/index.md).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
