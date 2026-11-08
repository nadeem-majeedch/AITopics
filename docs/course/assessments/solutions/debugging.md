# Debugging - solutions

```markdown
**Assessments:** [Overview](../index.md) · [Solutions](index.md) · [Debugging](../debugging.md)
```

Each entry gives the cause, the smallest fix, a regression test, and why the bug is
common. The symptoms quoted match runs on Python 3.12 with scikit-learn 1.x.

---

## DBG1 - Cross-validation accuracy 1.0 on noise

**Cause:** feature selection is fitted on all 40 rows, including the label, before
cross-validation. The 2,000 noise features are ranked by how well they separate the
labels in the *whole* dataset, so 50 features are chosen precisely because they correlate
with `y` by chance. Cross-validation then measures how well those preselected features
fit, not whether the procedure generalises. The measured values: **1.00 leaky, 0.70
honest**.

**Fix:** put selection inside a pipeline so it is refitted on each training fold:

```python
from sklearn.pipeline import make_pipeline
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

pipe = make_pipeline(SelectKBest(f_classif, k=50), LogisticRegression(max_iter=1000))
print(cross_val_score(pipe, X, y, cv=5).mean())
```

**Regression test:** with random labels, the pipeline's mean CV score must be near
chance (0.5 for balanced binary); assert it is below 0.75. Any preprocessing that uses
`y` - selection, target encoding, resampling - belongs inside the pipeline.

---

## DBG2 - Every fold scores near zero

**Cause:** the labels are sorted (15 zeros, then 15 ones) and `KFold(shuffle=False)`
takes contiguous blocks. The first fold's test block is all class 0 while its training
block contains only class 1, so the model predicts the only class it has seen and every
prediction is wrong. The scores are **[0.0, 0.17, 0.17, 0.0, 0.0]**; the model fits the
full data well, which is why the symptom looks paradoxical.

**Fix (two changes):** use `StratifiedKFold(n_splits=5, shuffle=True, random_state=0)`
so each fold contains both classes and the split is reproducible. Sorting rows by label
before splitting is the underlying mistake; if the data arrive sorted, shuffle once with
a recorded seed.

**Regression test:** assert that every fold's training labels contain both classes and
that each fold's score is above 0.5 on a separable synthetic set.

---

## DBG3 - Loss near 0.97 that barely moves

**Cause:** the logits have shape `(4,)` and the targets `(4, 1)`, so NumPy broadcasts to
`(4, 4)`: every prediction is compared with every target. The printed loss shape is
`(4, 4)` and its mean is **0.9701**, against **0.7201** for the correctly aligned
computation. Training on this loss optimises a matrix of cross terms, so the gradient
does not correspond to the model's outputs.

**Fix:** align the shapes once, at the boundary:

```python
targets = targets.reshape(-1)          # (4,)
loss = -(targets * np.log(p) + (1 - targets) * np.log(1 - p))
```

**Regression test:** assert `loss.shape == logits.shape`, and compare against a
hand-computed value for four known logits. Broadcasting bugs are silent; a shape
assertion is cheap.

---

## DBG4 - Test accuracy barely above chance

**Cause:** `X` and `y` are split twice, with different `random_state` values, so the test
features and test labels are not aligned. The model is trained correctly and then scored
against the wrong labels: **1.00 aligned, 0.556 misaligned**. No error is raised because
both arrays have the same length.

**Fix:** split once and unpack all four arrays together:

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=0, stratify=y
)
```

**Regression test:** assert that the split is a partition (`len(train) + len(test) ==
len(y)`) and that recomputing with the same seed gives identical indices. The general
rule: any two arrays that must stay aligned are split in one call, or indexed by the
same stored indices.

---

## DBG5 - WER crashes on an empty reference

**Cause:** the function divides by `len(ref)`, which is zero for a clip with no speech
or a missing reference. The exception is `ZeroDivisionError`; the code before it also
computes nonsense, since `(len(ref) + len(hyp))` is not a WER formula at all (it should
be `(S + D + I) / len(ref)`).

**Fix:** handle the degenerate case explicitly and refuse to score it silently:

```python
def wer(reference: str, hypothesis: str) -> float:
    ref, hyp = reference.split(), hypothesis.split()
    if not ref:
        if not hyp:
            return 0.0
        raise ValueError("empty reference with non-empty hypothesis: not scoreable")
    s, d, i = edit_counts(ref, hyp)      # your alignment
    return (s + d + i) / len(ref)
```

**Why returning 0.0 is also wrong:** it reports perfect accuracy for a clip that was
never transcribed, which biases the corpus average downward. Better to exclude the clip
from the average and report how many were excluded.

**Regression test:** empty/empty returns 0.0, empty/non-empty raises, and a known pair
with one insertion returns 0.25 for four reference words.

---

## DBG6 - Retrieval always returns document 0

**Cause:** tokenisation is case-sensitive and punctuation-attached. `"Refund"` is not
`"refund"`, and `"policy:"` is not `"policy"`, so the query's tokens appear in no
document. The raw scores are `[0, 0, 0]`; lowercasing both sides gives `[1, 0, 0]`.

**Fix:** one normalisation function applied to queries and documents at both index and
query time, and a test that the same function is used in both paths:

```python
import re
def normalise(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())
```

**Regression test:** for a query copied from a document with different case and
punctuation, the correct document must rank first. **Lesson:** normalisation applied to
only one side of a comparison is a silent recall killer, and it looks like "the model is
bad" rather than "the code is wrong".

---

## DBG7 - AP is 3.0

**Cause:** the function counts every prediction that matches a ground-truth box as a
true positive, without marking that box as already matched. One object and three
predictions all matching it produce recall `[1, 2, 3]`, precision `[1, 0.5, 0.6]`, and an
AP of **3.0** - above the maximum of 1.0, which is the clue.

**Fix:** match greedily by descending score and mark each ground-truth box as used;
extra predictions that hit a used box are false positives. With correct matching the AP
is **1.0** for this example (the first prediction is a true positive at precision 1.0,
the rest are false positives after recall is already 1.0).

**Regression test:** AP must lie in `[0, 1]`; assert that, and assert that duplicating a
prediction cannot increase AP. Reported mAP with this bug is inflated and can exceed 1,
which sometimes slips through because the average across classes hides it.
