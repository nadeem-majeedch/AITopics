# Debugging challenges

```markdown
**Assessments:** [Overview](index.md) · **Debugging** · [Solutions](solutions/debugging.md)
```

Seven failing programs with a reported symptom. For each: explain the cause, give
the smallest fix, and say what test would have caught it. Attempts are more useful
than reading the solution: reproduce the symptom yourself first.

Answers and fixed versions are in [solutions/debugging.md](solutions/debugging.md).

**Marking:** 4 = cause, fix, and a regression test; 3 = cause and fix; 2 = symptom
identified only; 1 = no progress.

---

## DBG1 - "Cross-validation accuracy is 1.0 on pure noise"

```python
import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

rng = np.random.default_rng(0)
X = rng.normal(size=(40, 2000))
y = rng.integers(0, 2, size=40)

selector = SelectKBest(f_classif, k=50).fit(X, y)
X_selected = selector.transform(X)
print(cross_val_score(LogisticRegression(max_iter=1000), X_selected, y, cv=5).mean())
```

**Symptom:** mean cross-validated accuracy is 1.00, and the data are random.
**Question:** why is the estimate invalid, and what is the honest score?

---

## DBG2 - "Every fold scores near zero"

```python
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold, cross_val_score

X = np.random.default_rng(2).normal(size=(30, 3))
y = np.array([0] * 15 + [1] * 15)

scores = cross_val_score(LogisticRegression(), X, y, cv=KFold(5, shuffle=False))
print(scores.round(2))
```

**Symptom:** scores are `[0. 0.17 0.17 0. 0.]` while the model fits the full data
well.
**Question:** what does each training fold contain, and which two changes fix it?

---

## DBG3 - "Loss is around 0.97 and barely moves"

```python
import numpy as np

logits = np.array([-2.0, -1.0, 1.0, 2.0])
targets = np.array([0, 1, 0, 1]).reshape(-1, 1)
p = 1 / (1 + np.exp(-logits))
loss = -(targets * np.log(p) + (1 - targets) * np.log(1 - p))
print(loss.shape, loss.mean())
```

**Symptom:** loss shape is `(4, 4)` and the reported value does not match a
hand-computed binary cross-entropy.
**Question:** explain the broadcast, and give the one-line fix.

---

## DBG4 - "Test accuracy is barely above chance"

```python
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
_, _, _, y_test_2 = train_test_split(X, y, test_size=0.3, random_state=1)

model = LogisticRegression().fit(X_train, y_train)
print(model.score(X_test, y_test_2))
```

**Symptom:** training accuracy is 1.0; the printed score is around 0.55.
**Question:** what is being compared, and why does `random_state` matter here?

---

## DBG5 - "WER crashes on one file"

```python
def wer(reference: str, hypothesis: str) -> float:
    ref, hyp = reference.split(), hypothesis.split()
    return (len(ref) + len(hyp)) / len(ref)
```

**Symptom:** `ZeroDivisionError` on a clip whose reference transcript is empty.
**Question:** what should the function return, and why is returning 0.0 also wrong?

---

## DBG6 - "Retrieval always returns the first document"

```python
docs = [
    "Refund policy: returns within 30 days.",
    "Delivery times and tracking.",
    "Account access and passwords.",
]

def score(query, doc):
    return len(set(query.split()) & set(doc.split()))

query = "Refund policy"
print([score(query, d) for d in docs])
```

**Symptom:** every score is 0, so the retriever falls back to document 0.
**Question:** why do the sets not intersect, and what is the general lesson about
normalising queries and documents?

---

## DBG7 - "AP is 3.0"

```python
import numpy as np

def average_precision(matches, n_gt):
    tp = np.cumsum(matches)
    fp = np.cumsum(1 - np.array(matches))
    precision = tp / (tp + fp)
    recall = tp / n_gt
    return float(np.sum(np.diff(np.concatenate([[0.0], recall])) * precision))

print(average_precision([1, 1, 1], n_gt=1))
```

**Symptom:** the function returns 3.0 for one ground-truth object and three
predictions.
**Question:** what rule is missing, what should the value be, and what does the bug
do to a reported mAP?
