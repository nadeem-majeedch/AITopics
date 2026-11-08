# Code-reading exercises

```markdown
**Assessments:** [Overview](index.md) · **Code reading** · [Solutions](solutions/code-reading.md)
```

Seven short programs. For each: state what it prints, then state what is wrong with
it or what it hides. Do not run them first; the point is to read code the way you
read a claim. Answers, including the exact printed values, are in
[solutions/code-reading.md](solutions/code-reading.md).

**Marking:** 4 = correct output and correct critique; 3 = correct output, thin
critique; 2 = one of the two; 1 = neither.

---

## CR1 - Numerical stability in a softmax

```python
import numpy as np

logits = np.array([1000.0, 1001.0])
naive = np.exp(logits) / np.exp(logits).sum()

shifted = logits - logits.max()
stable = np.exp(shifted) / np.exp(shifted).sum()
print(naive, stable.round(4))
```

1. What is printed?
2. Why does the second version give a usable answer when the first does not?
3. The two versions are mathematically equal. What property of floating point breaks
   the equality?

---

## CR2 - Target encoding before the split

```python
import pandas as pd

df = pd.DataFrame({
    "customer": ["a", "a", "b", "b", "c", "c"],
    "churn":    [0, 1, 0, 0, 1, 1],
})
df["cust_mean"] = df.groupby("customer")["churn"].transform("mean")
print(df.loc[0, "cust_mean"])
```

1. What is printed for row 0?
2. What is printed for customer `c`?
3. Explain why this feature would be useless or harmful in a churn model, and how
   to compute it safely.

---

## CR3 - An accuracy function that never raises

```python
def accuracy(y_true, y_pred):
    return sum(a == b for a, b in zip(y_true, y_pred)) / len(y_true)

print(accuracy([1, 0, 1, 1, 0], [1, 0, 1, 1]))
```

1. What is printed?
2. Why is that number wrong rather than an error?
3. Write the two lines you would add to make this failure impossible.

---

## CR4 - A stratified split you did not check

```python
from sklearn.model_selection import train_test_split

y = [0] * 8 + [1] * 4
X = list(range(12))
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=0
)
print(len(y_train), sum(y_train), len(y_test), sum(y_test))
```

1. What is printed?
2. Is the test set large enough to estimate recall for the positive class? What is
   the smallest change in the number of true positives that would move recall?
3. What would you report alongside the metric?

---

## CR5 - A seeding misconception

```python
import numpy as np

np.random.seed(0)
a = np.random.rand(2)

np.random.seed(0)
b = np.random.rand(3)

print(np.allclose(a, b[:2]), a.round(4))
```

1. What is printed?
2. A colleague concludes "seeding makes runs identical". Give one reason this
   conclusion is too strong.

---

## CR6 - Tie-breaking in a ranking

```python
import numpy as np

scores = np.array([0.50, 0.50, 0.90, 0.50])
order = np.argsort(scores)[::-1]
print(order, order[:2])
```

1. What is printed?
2. Three documents share a score of 0.50. Which one is ranked second, and why?
3. Why can two implementations with identical scores return different top-k lists,
   and what should an evaluation do about it?

---

## CR7 - The compression ratio you report

```python
params = 1_200_000
float32_bytes = params * 4
int8_bytes = params * 1
scales_bytes = (params // 64) * 4
print(float32_bytes, int8_bytes + scales_bytes, round(float32_bytes / (int8_bytes + scales_bytes), 2))
```

1. What is printed?
2. A report says "4x smaller". Is that right? Explain the difference.
3. Name one thing this arithmetic ignores that affects real deployment size.
