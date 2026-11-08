# Code reading - solutions

```markdown
**Assessments:** [Overview](../index.md) · [Solutions](index.md) · [Code reading](../code-reading.md)
```

Printed values below were produced by running the snippets on Python 3.12 with NumPy
2.x. Floating-point output is rounded as shown; your exact digits may differ in the
last place.

---

## CR1 - Numerical stability in a softmax

**Prints** `[nan nan] [0.2689 0.7311]` and emits a runtime warning about overflow in
`exp`.

`np.exp(1000)` exceeds the largest representable float, so it becomes `inf`; `inf /
inf` is `nan`. Subtracting the maximum gives `[0, -1]`, whose exponentials are `1` and
`0.3679`, and the ratio is well conditioned. The two expressions are equal in real
arithmetic; floating point breaks the equality because the intermediate exponentials
are not representable. **Lesson:** implement softmax and log-sum-exp in the shifted
form, and never compute `exp` of an unshifted logit.

## CR2 - Target encoding before the split

**Prints** `0.5` for row 0, and `1.0` for both rows of customer `c`.

The encoding is computed with each row's own label included: customer `c` has two rows,
both churn = 1, so the mean is 1.0. That value is a summary of the target for that
customer, and using it as a feature leaks the label. In a real pipeline it is worse
than useless: at prediction time a new customer has no rows, so the feature is
undefined. **Safe version:** compute the encoding inside each training fold, map unseen
categories to the global prior, and never compute it on the full dataset before
splitting. **Lesson:** any feature computed with `groupby(...).transform(...)` over the
target is a leak until proven otherwise.

## CR3 - An accuracy function that never raises

**Prints** `0.8`.

`zip` stops at the shorter sequence, so four comparisons are made and all four match;
the sum is 4 and the denominator is `len(y_true) = 5`, giving 0.8. The function reports
a plausible number for misaligned inputs, which is worse than crashing because nothing
draws attention to it. **Fix:** validate before computing, for example
`assert len(y_true) == len(y_pred) and len(y_true) > 0`, or use
`zip(..., strict=True)` on Python 3.10+, which raises on length mismatch. **Lesson:** a
metric function should fail loudly on malformed input; silent coercion is how wrong
numbers reach reports.

## CR4 - A stratified split you did not check

**Prints** `9 3 3 1`.

The test set has three rows, one positive. Recall can only be 0 or 1, and a single
different prediction changes it by 1.0, so the metric is not an estimate of anything.
You would report the counts (`1 of 3 positives`), an interval, and a caveat; better,
choose a larger test fraction or repeated splits. **Lesson:** stratification preserves
the ratio, not the sample size; a metric on three rows is a description of three rows.

## CR5 - A seeding misconception

**Prints** `True [0.5488 0.7152]`.

Reseeding the global generator produces the same stream, so the first two draws match.
The conclusion is too strong because the stream depends on call order and on the number
of draws: inserting one extra random call shifts everything after it. Different library
versions, thread counts, and GPU kernels can also change results despite a seed. **What
to say instead:** "at this version, on this hardware, with this call order, the run
reproduces"; record versions and average over seeds when the claim matters.

## CR6 - Tie-breaking in a ranking

**Prints** `[2 3 1 0] [2 3]`.

`argsort` returns ascending order with ties broken by position (`[0, 1, 3]` for the
0.50s); reversing puts index 3 before 1 and 0, so the second result is document 3, not
document 1. Two libraries can break ties differently, so the top-k list is not
deterministic even when the scores are identical. **What an evaluation should do:**
define a total order (score descending, then id ascending), apply it explicitly, and
state it. **Lesson:** ties are a specification problem; do not let a library decide
your reported ranking.

## CR7 - The compression ratio you report

**Prints** `4800000 1275000 3.76`.

The float32 weights are 4.8 MB. The int8 weights are 1.2 MB, and one float32 scale per
64 weights adds 75,000 bytes, so the quantised artifact is 1,275,000 bytes and the
ratio is 3.76, not 4. The "4x" claim is the ideal ratio and overstates the real
reduction. **What the arithmetic ignores:** alignment and container overhead, model
metadata, the tokeniser or label map, optimiser state if you ship it, and any layers
kept in higher precision. **Lesson:** measure the artifact you ship, not the parameter
count times bytes per parameter.
