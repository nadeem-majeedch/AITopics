# F11 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F11 is self-assessed against published criteria. There is no proctored exam and
no credit is awarded. Keep your evidence and decide whether you are ready for
F12.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook, printed outputs, two figures |
| Independent lab | 40% | Noisy XOR capacity study and report |
| Reflection | 10% | 200-300 words |

## Part A - Knowledge check (20%)

Answer in your own words before opening the answer. Each question is worth 2.5
points; a correct number without a reason earns half credit.

**1. A perceptron has `w1 = 1`, `w2 = 1`, and `b = -0.5`. Compute the output for
`(x1, x2) = (1, 0)` and state what logical function the unit implements.**

??? note "Answer"
    `z = 1*1 + 1*0 - 0.5 = 0.5`. The step function returns 1 because `z >= 0`.
    With these weights the unit implements OR: only `(0, 0)` produces a negative
    pre-activation and therefore 0.

**2. Why can no single perceptron implement XOR, even with carefully chosen
weights?**

??? note "Answer"
    XOR is not linearly separable. The class-0 points `(0,0)` and `(1,1)` lie on
    one diagonal and the class-1 points `(0,1)` and `(1,0)` on the other, so the
    diagonals cross. A perceptron can only place one line (hyperplane) in input
    space, and no line puts the two class-0 points on one side and the two
    class-1 points on the other. Adding a bias moves the line but does not change
    this geometry.

**3. The notebook builds XOR from two hidden units. What does each hidden unit
compute, and what does the output unit compute?**

??? note "Answer"
    One hidden unit computes OR (`x1 + x2 - 0.5 >= 0`) and the other computes AND
    (`x1 + x2 - 1.5 >= 0`). The output computes `OR - AND - 0.5`, which is 1
    exactly when one input is 1 and the other is 0. The hidden layer creates a
    representation in which XOR becomes linearly separable.

**4. An MLP has hidden layers `(3, 8)`, `(8, 4)`, and an output of 1 unit.**
**Compute the trainable parameter count, showing each layer.**

??? note "Answer"
    Layer 1: `3*8 + 8 = 32`. Layer 2: `8*4 + 4 = 36`. Output: `4*1 + 1 = 5`.
    Total: `32 + 36 + 5 = 73` parameters. Weights and biases both count.

**5. Read this line from the notebook. What does it print, and why is the shape
not `(16, 2)`?**

```python
print(mlp.coefs_[0].shape)
```

??? note "Answer"
    It prints `(2, 16)`. scikit-learn stores each weight matrix as
    `(n_inputs, n_outputs)`, so the first layer maps 2 input features to 16
    hidden units. The transpose shape would count the same numbers but would not
    match the multiplication `X @ W` used internally.

**6. What is a dead ReLU, and what symptom would it produce during training?**

??? note "Answer"
    A dead ReLU is a unit whose pre-activation is negative for every input it
    sees, so it outputs 0 and its gradient is 0. Its weights stop updating. Many
    dead units reduce effective capacity and show up as underfitting: training
    loss stalls at a high value and additional epochs do not help.

**7. The notebook scales features with `StandardScaler` fitted on the training
split. What goes wrong if you fit the scaler on the full dataset before
splitting?**

??? note "Answer"
    The scaler's mean and standard deviation then depend on the test rows, so
    information from the test set leaks into training. The reported test accuracy
    becomes optimistic and no longer estimates performance on unseen data. Fit on
    training data, then transform validation and test with those same statistics.

**8. The notebook reports MLP test accuracy 0.94 against logistic regression 0.86.**
**Name two reasons this does not yet justify deploying the MLP.**

??? note "Answer"
    Any two of: it is a single split of 150 synthetic test points, so sampling
    noise is large; there is no seed variation or confidence interval; there is no
    per-class error analysis or confusion matrix; the data is synthetic and may
    not represent real sensors; no calibration, latency, or maintenance cost was
    measured; no baseline tuning was attempted for logistic regression.

**Self-score:** 2.5 points per question. Award full credit only when the answer
contains the mechanism, not just the conclusion.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10% | All six sections executed top to bottom in a clean kernel |
| Correctness | 10% | Assertions pass; OR, both XOR outputs, shapes, and 193 parameters are present |
| Interpretation | 10% | A short markdown note explaining why the MLP beats logistic regression and one limitation of the result |

A notebook with outputs but no interpretation scores at most 20 of 30. Add the
note under the final section, not in a separate file.

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric): technical correctness 30%, evaluation and diagnosis
25%, reproducibility 15%, data and ethics 15%, communication 15%.

| Dimension | Points |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |
| **Total** | **100** |

Common reasons for losing marks:

- Reporting accuracy for one seed only.
- Choosing the widest model because it scored 0.01 higher once.
- Splitting the whole table instead of splitting within each corner.
- Fitting the scaler before the split.
- Quoting a parameter count that does not match the printed shapes.
- Claiming a test accuracy of 1.00 on noisy XOR without investigating leakage.
- Describing a teaching model as ready for sensor hardware.

## Part D - Reflection (10%)

Write 200-300 words and answer all three prompts:

1. Which idea became clearer when you built XOR by hand: linear separability, the
   role of a hidden layer, or the role of the activation? Give a concrete moment
   from your work.
2. Your lab measured spread across seeds. How did that change the way you read the
   notebook's single 0.94?
3. What will you check first the next time a neural network trains but performs no
   better than a linear baseline?

Reflection is not a summary of steps. It is reasoning about evidence and what you
will do differently.

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
| 90-100 | Ready for F12; evidence is complete and reproducible |
| 75-89 | Ready, but fix the weakest rubric dimension first |
| 60-74 | Reread the lesson and rerun the notebook; lab evidence has gaps |
| Below 60 | Repeat the module before starting backpropagation |

These bands are for planning. They are not a university grade.

## Academic integrity and AI assistance

- You may use an AI assistant to explain an error or suggest a debugging step.
- You must run the code, generate the data, and record the numbers yourself.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and what you verified independently.
- Do not submit results for runs you did not perform, and do not copy another
  student's `results.csv`.

The course policy is in
[Academic integrity](../../course/assessments.md#academic-integrity) and
[How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight questions before opening the answers.
- [ ] My notebook ran from a clean kernel and both figures exist.
- [ ] My lab has `results.csv` with five seeds per width.
- [ ] My three validation checks passed and are shown in the report.
- [ ] My capacity decision follows the stated reliability bar.
- [ ] My reflection addresses all three prompts.
- [ ] I removed personal paths and hostnames from the submission.

**Next:** [F12 - Backpropagation](../f12-backpropagation/index.md) explains how
the 193 weights are learned. The module plan is
[M03](../../syllabus/level-1-foundations.md#m03).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
