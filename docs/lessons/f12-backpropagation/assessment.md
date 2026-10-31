# F12 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F12 is self-assessed. There is no proctored exam and no credit is awarded. Keep
your curves and run logs as evidence.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook, gradient check, parameter count, curve figure |
| Independent lab | 40% | Training-curve diagnosis on the pilot dataset |
| Reflection | 10% | 200-300 words |

## Part A - Knowledge check (20%)

Each question is worth 2.5 points. Answer before opening the answer.

**1. Code reading. What does this print, and why?**

```python
x = torch.tensor(2.0, requires_grad=True)
y = 3 * x**2 + x
y.backward()
print(x.grad.item())
```

??? note "Answer"
    It prints `13.0`. The derivative of `3x^2 + x` is `6x + 1`, which is 13 at
    `x = 2`. `backward()` applies the chain rule and stores the result in
    `x.grad`. If `x` had been created without `requires_grad=True`, the call would
    fail because no graph was recorded.

**2. Why is `optimizer.zero_grad()` needed before each backward pass?**

??? note "Answer"
    PyTorch accumulates gradients in `.grad` by adding new values. Without
    resetting, each step uses the sum of all previous gradients, so the effective
    step size grows and the update is wrong. `zero_grad()` clears the buffers
    before computing the current gradient.

**3. Compute the trainable parameter count of `Linear(4, 32)`,
`Linear(32, 8)`, `Linear(8, 1)`. Show each layer.**

??? note "Answer"
    `4*32 + 32 = 160`; `32*8 + 8 = 264`; `8*1 + 1 = 9`. Total
    `160 + 264 + 9 = 433` parameters.

**4. What does `BCEWithLogitsLoss` expect as model output, and why is it
preferred over sigmoid followed by `BCELoss`?**

??? note "Answer"
    It expects raw logits, not probabilities, and targets shaped like the logits.
    It fuses the sigmoid with the cross-entropy computation in a numerically
    stable form, avoiding overflow or underflow for large logits and avoiding the
    double-sigmoid mistake that happens when a sigmoid is applied twice.

**5. The notebook reports analytic gradient `-0.346939` and numeric gradient
`-0.346988`. Are these consistent? What explains the difference?**

??? note "Answer"
    Yes. They agree to about `5e-5`, far inside the `1e-2` tolerance. A central
    finite difference approximates a limit with a finite `eps = 1e-3`, so it
    carries truncation error; floating-point rounding adds a small error too. An
    exact match would be suspicious.

**6. A model has training loss 0.12 and validation loss 0.18 at epoch 200.
Validation loss was 0.15 at epoch 50 and has risen since. Validation accuracy
is stable at 0.945. Diagnose the situation and name one next action.**

??? note "Answer"
    The model is overfitting: training loss keeps falling while validation loss
    rises, and the gap widens after epoch 50. Stable accuracy with rising loss
    means the model is becoming more confident, including on wrong examples.
    Reasonable actions: early stopping around epoch 50, weight decay, a smaller
    model, or more training data. Adding epochs would make it worse.

**7. Why does replacing both ReLU layers with `nn.Identity()` reduce accuracy even
though the parameter count does not change?**

??? note "Answer"
    Composing linear layers without a nonlinearity produces another linear
    function. The three layers collapse to a single linear map, so the model can
    only draw a straight decision boundary, like logistic regression. The weights
    still exist and are still trained; they simply cannot represent a curved
    boundary.

**8. What is the difference between a logit and a probability, and why does
training use the logit?**

??? note "Answer"
    A logit is an unbounded real score; a probability is the logit passed through
    a sigmoid, confined to `(0, 1)`. Training on logits keeps the loss computation
    stable and keeps gradients well scaled. Convert to probabilities only for
    reporting, thresholding, or calibration.

**Self-score:** 2.5 points each. Award full credit only when the answer explains
the mechanism.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10% | All six sections executed top to bottom; curve figure saved |
| Correctness | 10% | Derivative 7.0, gradient check within tolerance, 337 parameters, validation above 0.90 |
| Interpretation | 10% | A short note identifying the epoch where validation loss turns and what that implies |

Add the interpretation as markdown under the curves section. A pasted figure with
no comment scores at most 20 of 30.

## Part C - Independent lab (40%)

Scored with the five-dimension rubric on the [lab brief](lab.md#rubric):
technical correctness 30%, evaluation and diagnosis 25%, reproducibility 15%,
data and ethics 15%, communication 15%.

| Dimension | Points |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |
| **Total** | **100** |

Common reasons for losing marks:

- Leaving `final_score` in the features and reporting near-perfect accuracy.
- Plotting curves but never naming the best epoch or the gap.
- Changing architecture, learning rate, and epochs at the same time.
- Tuning the stopping epoch against the test set.
- Reporting one seed for the final recipe without saying so.
- Presenting a synthetic-data model as a real student screening tool.

## Part D - Reflection (10%)

Write 200-300 words and answer all three prompts:

1. Which part of the training step was least intuitive before you computed it by
   hand, and what made it concrete?
2. Your lab required a diagnosis before any change. How did writing the diagnosis
   first alter what you tried?
3. What evidence would you require before believing a claimed accuracy
   improvement in someone else's notebook?

Reflection is reasoning about evidence, not a summary of the steps.

## Scoring worksheet

| Component | Maximum | Your score | Notes |
| --- | --- | --- | --- |
| Knowledge check (8 x 2.5) | 20 | | |
| Guided notebook | 30 | | |
| Independent lab | 40 | | |
| Reflection | 10 | | |
| **Total** | **100** | | |

Self-study bands:

| Score | Interpretation |
| --- | --- |
| 90-100 | Ready for F13; evidence is complete and reproducible |
| 75-89 | Ready, but fix the weakest rubric dimension first |
| 60-74 | Reread the lesson and rerun the notebook; lab evidence has gaps |
| Below 60 | Repeat the module before starting reproducibility work |

These bands are for planning. They are not a university grade.

## Academic integrity and AI assistance

- You may use an AI assistant to explain an error or suggest a diagnostic step.
- You must run the training, produce the curves, and record the numbers yourself.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and what you verified independently.
- Do not submit curves or run logs you did not generate.

The course policy is in
[Academic integrity](../../course/assessments.md#academic-integrity) and
[How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight questions before opening the answers.
- [ ] My notebook ran from a clean kernel and the curve figure exists.
- [ ] My lab excludes `final_score` and shows the feature list.
- [ ] My diagnosis cites a best epoch and a train-validation gap.
- [ ] Each controlled change altered exactly one factor.
- [ ] The test set was evaluated once, after freezing the configuration.
- [ ] My reflection addresses all three prompts.
- [ ] No personal paths remain in the submission.

**Next:** [F13 - Reproducibility](../f13-reproducibility/index.md) turns these runs
into a record another person can repeat. The module plan is
[M03](../../syllabus/level-1-foundations.md#m03).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
