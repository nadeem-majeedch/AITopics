# F11 lab - How much hidden capacity does noisy XOR need?

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F11 module score |
| **Time** | About 3 hours |
| **Hardware** | CPU-only; a GPU gives no advantage at this size |
| **Starter file** | `labs/foundations/f11_xor_mlp.md` |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The scenario

A robotics club built a two-bit optical sensor that reports whether each of two
slots is blocked. The signal they actually need is **odd parity**: exactly one
slot blocked, which is XOR. The sensors are not clean. Each reading carries
Gaussian noise of about 0.18 units, and the club measured 400 readings with known
labels.

The club's sponsor will approve a model only if it is **reliable across repeated
training runs**, not lucky once. Your job is to find the smallest hidden-layer
width that clears a stated reliability bar, and to justify the choice with
evidence. A second, larger model that scores the same is not an improvement; it
is extra capacity the problem does not need.

!!! note "Why this is not the notebook again"
    The notebook hand-builds XOR with step units and trains on `make_moons`. This
    lab generates a noisy XOR dataset from scratch, controls the split yourself,
    repeats training across seeds, and asks for a capacity decision. None of
    those steps appear in the notebook.

## What you must decide

Pick the smallest architecture from the candidate list that satisfies **both**
conditions on the held-out test set, averaged over five seeds:

- mean accuracy at least **0.90**;
- standard deviation across seeds no more than **0.02**.

If no candidate meets both, report the best one and explain why the bar was not
met. A justified "the bar is too strict for this noise level" is a valid finding;
an unsupported claim is not.

Candidate widths: `(2,)`, `(4,)`, `(16,)`, `(16, 16)`. All use ReLU and the same
solver, scaling, split, and epoch budget.

## Required steps

### Step 1 - Generate the dataset

Write a script or notebook that creates 100 samples per corner of the XOR square,
adds Gaussian noise with `sigma=0.18`, and assigns the XOR label.

```python
rng = np.random.default_rng(2026)
corners = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
labels = np.array([0, 1, 1, 0])
X = np.repeat(corners, 100, axis=0) + rng.normal(0, 0.18, size=(400, 2))
y = np.repeat(labels, 100)
```

Record the generator seed, the noise level, and the class balance. Save the
generated table as `xor_noisy.csv` so another student can audit it.

### Step 2 - Split inside each corner

Split each corner's 100 samples into 60 train, 20 validation, and 20 test. Do this
per corner, not once over the whole table, so all four corners appear in every
split in the same proportion.

**Validation check 1:** print the corner counts in each split. Each corner must
contribute 60 training, 20 validation, and 20 test rows, so the splits hold
240/80/80 rows in total and the label balance is 50/50 within rounding. If a
split is missing a corner, stop and fix the split before training.

### Step 3 - Fit the scaler on training data only

Standardize with `StandardScaler` fitted on the 240 training rows. Transform the
validation and test rows with that same fitted scaler.

**Validation check 2:** the transformed training features must have mean close to
0 and standard deviation close to 1. The test set's mean will not be exactly 0,
and that is correct: fitting the scaler on test data is leakage.

### Step 4 - Establish the linear baseline

Train logistic regression on the same scaled training data and evaluate on
validation and test.

Expected observation: accuracy near chance (roughly 0.40-0.60). XOR is not
linearly separable. A baseline far above 0.65 means your labels, corners, or
split are wrong; diagnose before continuing.

### Step 5 - Train the four candidate widths across five seeds

For each width in `(2,)`, `(4,)`, `(16,)`, `(16, 16)` and each seed in
`[0, 1, 2, 3, 4]`, train an `MLPClassifier` with `activation="relu"`,
`solver="adam"`, `max_iter=2000`, and the same `random_state=seed`. Keep every
other setting fixed.

Record for each run: width, seed, train accuracy, validation accuracy, test
accuracy, and wall-clock training time. Also record the parameter count computed
from the shapes, not copied from a blog post.

**Validation check 3:** repeat seed 0 for width `(16,)` twice. The two accuracies
must match to four decimal places. If they do not, your seeding or your data
generation is not controlled.

### Step 6 - Diagnose underfitting and overfitting

For every width, compare train and test accuracy:

- train and test both low, close together: **underfitting**;
- train high, test clearly lower: **overfitting**;
- train and test both high and close: the model fits this noise level.

State explicitly which widths underfit, which overfit, and which are appropriate.
Support each claim with numbers, not adjectives. Note that the noise places a
ceiling below 1.00, so a test accuracy of 1.00 would suggest leakage or a broken
split.

### Step 7 - Make and defend the decision

Apply the reliability bar from "What you must decide". Report mean and standard
deviation per width in a table and choose one architecture.

Then answer: if the club doubles the noise to 0.36, would your choice change?
You do not have to run that experiment, but you must reason about it in two or
three sentences.

### Step 8 - Produce the evidence pack

Assemble the report described below, including one figure with validation
accuracy per seed for each width (for example a strip plot or a small table
rendered as a bar chart with error bars). Redact personal paths.

## Deliverables

```text
f11-xor-lab/
  README.md                 # how to rerun, in 5-10 lines
  xor_lab.ipynb             # or xor_lab.py, executed end to end
  xor_noisy.csv             # 400 generated rows with labels
  results.csv               # one row per width and seed
  capacity.png              # accuracy per width with spread
  report.md                 # follows the template below
  reflection.md             # 200-300 words
```

`results.csv` must contain at least these columns: `width`, `seed`,
`train_acc`, `val_acc`, `test_acc`, `params`, `seconds`.

## Report template

Copy these headings into `report.md`:

```markdown
# F11 noisy XOR capacity report

## 1. Question and decision
The reliability bar, the candidates, and the width you chose.

## 2. Data and split
Generator seed, noise level, corner counts per split, class balance.

## 3. Method
Scaling, model settings, seeds, and the exact command that reproduces the run.

## 4. Results
Mean and standard deviation per width, plus the per-seed table.

## 5. Diagnosis
Which widths underfit or overfit, with evidence.

## 6. Decision and limits
Why the chosen width is justified; what would change your mind.

## 7. Reproduction
Commands, package versions, hardware, and runtime.

## 8. Ethics and privacy
Confirmation that the data is synthetic, no personal data is included, and the
model is a teaching artifact, not a certified sensor component.
```

## Rubric

The lab is scored out of 100 using the course's five dimensions.

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | Data generation, split, scaling, and training are correct; parameter counts match the shapes; all three validation checks pass | Model trains but the split or scaler is flawed, or counts are copied rather than computed |
| Evaluation and diagnosis | 25 | Under- and overfitting are identified per width with numbers; the decision follows the stated bar; the noise ceiling is recognized | Metrics reported without diagnosis; decision based on one seed |
| Reproducibility | 15 | Seeds, generator parameters, versions, commands, and hardware reproduce the table | Partial seeds or missing commands; another student could not rerun it |
| Data and ethics | 15 | Synthetic-data provenance documented; no personal data; no deployment or safety claims | Provenance vague or the report implies the model is production-ready |
| Communication | 15 | Clear tables, readable figure, honest limitations | Disorganized report or unsupported claims |

A dimension with no evidence scores zero. Numbers without an interpretation earn
at most half of the evaluation dimension.

## Privacy and safety constraints

- The dataset is synthetic. Do not replace it with real sensor logs from a
  workplace without written permission and a privacy review.
- Do not commit the virtual environment, caches, or notebook checkpoints.
- Remove usernames, absolute paths, and hostnames from logs and screenshots.
- Do not describe the model as safety-certified, production-ready, or suitable
  for controlling physical equipment. It is a teaching artifact.
- Report compute time honestly. Do not estimate timings you did not measure.

## Self-check before submission

- [ ] I generated 400 samples and can reproduce the exact table from the seed.
- [ ] Corner counts per split are 60/20/20 rows, totaling 240/80/80, and I showed
      them.
- [ ] The scaler was fitted on training data only.
- [ ] The logistic baseline is near chance, as expected for XOR.
- [ ] I trained all four widths across five seeds and kept settings fixed.
- [ ] My parameter counts match the printed shapes.
- [ ] I named which widths underfit or overfit and cited numbers.
- [ ] My decision follows the stated reliability bar.
- [ ] My report includes commands, versions, hardware, and runtime.
- [ ] No personal paths or identifying information remain.

Next: score the work with the [assessment](assessment.md), then continue to
[F12 - Backpropagation](../f12-backpropagation/index.md).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
