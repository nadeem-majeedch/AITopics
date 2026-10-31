# F11 - Neural network fundamentals {#f11}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Foundations (implements [M03](../../syllabus/level-1-foundations.md#m03)) |
| **Study time** | 10 hours: 2 h theory, 4 h guided notebook, 3 h lab, 1 h assessment |
| **Hardware** | CPU or GPU. The guided notebook is CPU-only and finishes in seconds. |
| **Prerequisites** | [F10 - Metrics and validation](../f10-metrics-validation/index.md); matrix multiplication; the derivative as a slope |
| **You will produce** | An executed notebook, a hand-built XOR network, two figures, an independent noisy-XOR experiment, and a short reflection |

## Why this module exists

A quality-control team records two sensor measurements for every part that comes
off a line. Parts that pass and parts that fail form two interleaved crescents:
no straight line separates them. A logistic regression reaches **0.86** accuracy
on held-out parts. A small neural network with two hidden layers reaches
**0.94** on exactly the same split.

The team now has three questions that this module answers:

1. What did the network add that the linear model could not represent?
2. Is 0.94 real, or an accident of one split of 150 test points?
3. What would make the result worse, and how would they notice?

A **neural network** is a stack of simple functions, each followed by a nonlinear
**activation**, trained by adjusting numeric **weights**. The stack can bend the
decision boundary, but it can also bend around noise. Knowing which is happening
is the engineering skill, not the library call.

!!! note "What this module is not"
    You will not build a large model here. The network in this module has 193
    parameters and runs in under a second. Depth, data pipelines, and GPU
    training come later.

## Learning objectives

By the end of this module, you can:

1. Describe a perceptron as a weighted sum plus a threshold, and compute its
   output for a small truth table.
2. Explain why no single linear boundary can implement XOR, using the geometry
   of the four input points.
3. Build a two-layer network by hand from OR and AND hidden units and show that
   it computes XOR.
4. Choose an activation function for a hidden layer and explain why removing
   nonlinearity collapses the network into a single linear map.
5. Read an MLP's weight shapes and compute its trainable parameter count without
   running code.
6. Compare an MLP with logistic regression on the same nonlinear split and
   interpret the result, including its uncertainty.
7. Explain when a curved decision boundary is evidence of learning and when it is
   evidence of overfitting.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| A working Python 3.12 environment from [M01](../m01-environment/index.md) | The notebook imports NumPy, scikit-learn, and matplotlib |
| `jupyterlab`, `scikit-learn`, `numpy`, `matplotlib` installed | `python -m pip install -r requirements/cpu.txt` covers all of them |
| F10 completed, especially accuracy, baselines, and overfitting | You will compare 0.86 and 0.94 against a baseline |
| Comfort with matrix shapes such as `(2, 16)` | Parameter counting depends on reading shapes correctly |
| 15 minutes of uninterrupted CPU time | Enough for the notebook plus one capacity experiment |

No GPU is required. If you have one, this module does not use it; PyTorch device
handling starts in [F12](../f12-backpropagation/index.md).

## The concepts you need

### 1. A neuron is a weighted sum plus a decision rule

A **weight** is a number that scales one input. A **bias** is a constant added
after the sum and shifts the decision threshold. The **pre-activation** is

```text
z = w1*x1 + w2*x2 + ... + b
```

An **activation function** turns `z` into the unit's output. The original
**perceptron** uses a step function: output 1 when `z >= 0`, otherwise 0.

With `w1 = 1`, `w2 = 1`, and `b = -0.5`, the unit implements logical OR:

| x1 | x2 | z = x1 + x2 - 0.5 | step(z) |
| --- | --- | --- | --- |
| 0 | 0 | -0.5 | 0 |
| 0 | 1 | 0.5 | 1 |
| 1 | 0 | 0.5 | 1 |
| 1 | 1 | 1.5 | 1 |

The equation `w1*x1 + w2*x2 + b = 0` is a **decision boundary**: a line in two
dimensions, a plane in three, and a hyperplane in general. The bias moves that
line; the weights rotate it.

### 2. Why one layer stops at XOR

**Linear separability** means one straight line can put all points of one class
on one side and all points of the other class on the other side. XOR is not
linearly separable.

| x1 | x2 | OR | AND | XOR |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0 |
| 0 | 1 | 1 | 0 | 1 |
| 1 | 0 | 1 | 0 | 1 |
| 1 | 1 | 1 | 1 | 0 |

Plot the four points: `(0,0)` and `(1,1)` must be class 0; `(0,1)` and `(1,0)`
must be class 1. The two class-0 points sit at opposite corners, and the two
class-1 points sit at the other opposite corners. The diagonals joining each pair
cross at the center, so the two classes cannot be separated by one line. The
notebook demonstrates the failure directly:

```python
or_output = perceptron(inputs[:, 0], inputs[:, 1])          # [0, 1, 1, 1]
xor_output = perceptron(inputs[:, 0], inputs[:, 1], bias=-0.5)
# [0, 1, 1, 1] but the target is [0, 1, 1, 0]
```

The single unit is not broken. Its hypothesis class, the set of functions it can
represent, simply does not contain XOR.

### 3. A hidden layer changes the geometry

A **hidden layer** is a layer between the inputs and the output. Its units
create new features that the output unit can combine linearly. Two hidden units
are enough for XOR: one computes OR, the other computes AND, and the output
computes `OR - AND`.

| x1 | x2 | hidden OR | hidden AND | OR - AND - 0.5 | step |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | -0.5 | 0 |
| 0 | 1 | 1 | 0 | 0.5 | 1 |
| 1 | 0 | 1 | 0 | 0.5 | 1 |
| 1 | 1 | 1 | 1 | -0.5 | 0 |

```python
def two_layer_xor(x1, x2):
    hidden_or = step(x1 + x2 - 0.5)
    hidden_and = step(x1 + x2 - 1.5)
    return step(hidden_or - hidden_and - 0.5)
```

In the new two-dimensional space `(OR, AND)`, the four points are `(0,0)`,
`(1,0)`, `(1,0)`, `(1,1)`: now a line separates class 0 from class 1. The hidden
layer did not add information; it changed the **representation** so that a linear
output unit could finish the job.

This hand-built network is not trained. Training means finding weights that make
the hidden units useful on their own, which is what backpropagation does in
[F12](../f12-backpropagation/index.md).

### 4. Activation functions: nonlinearity is the point

Composing linear functions gives another linear function. A stack of ten linear
layers is therefore equivalent to one matrix, no matter how wide it is. The
activation between layers is what makes depth meaningful.

| Activation | Range | Derivative | Typical use | Main risk |
| --- | --- | --- | --- | --- |
| Step | `{0, 1}` | 0 almost everywhere | Perceptron history, teaching | No gradient, cannot train by descent |
| Sigmoid | `(0, 1)` | `s * (1 - s)` | Output probability, shallow historical nets | Saturates; gradients shrink |
| Tanh | `(-1, 1)` | `1 - tanh(z)^2` | Hidden layers in small networks | Saturates like sigmoid |
| ReLU | `[0, inf)` | 0 or 1 | Default hidden activation | A unit stuck on negative input is **dead** |

```python
relu = lambda z: np.maximum(0, z)
sigmoid = lambda z: 1 / (1 + np.exp(-z))
```

**ReLU** means rectified linear unit. It is cheap and does not saturate for
positive input. A **dead ReLU** always outputs 0 because its weights only ever
produced negative pre-activations; it contributes nothing and receives no
gradient. A network with many dead units underfits.

### 5. Shapes, parameters, and capacity

The notebook's trained model has two hidden layers of 16 and 8 units. The
weight matrices follow the layer sizes, and every unit adds one bias:

| Layer | Weight shape | Bias shape | Parameters |
| --- | --- | --- | --- |
| Input to hidden 1 | `(2, 16)` | `(16,)` | `2*16 + 16 = 48` |
| Hidden 1 to hidden 2 | `(16, 8)` | `(8,)` | `16*8 + 8 = 136` |
| Hidden 2 to output | `(8, 1)` | `(1,)` | `8*1 + 1 = 9` |
| **Total** | | | **193** |

The network has 25 units but 193 trainable parameters. **Capacity** is the
network's ability to fit varied functions; parameter count is a rough proxy.

| Architecture | Parameters | Comment |
| --- | --- | --- |
| `(8,)` | `2*8 + 8 + 8*1 + 1 = 33` | Small; may underfit a curved boundary |
| `(16, 8)` | 193 | The notebook's model |
| `(64, 64)` | `2*64 + 64 + 64*64 + 64 + 64 + 1 = 4417` | Much more capacity, more overfitting risk |

### 6. Loss, optimization, and the decision boundary

Training needs a number to reduce. A **loss function** measures how wrong the
predictions are; scikit-learn's `MLPClassifier` minimizes **log loss** (also
called cross-entropy) for classification. An **optimizer** adjusts the weights in
the direction that lowers the loss. F12 opens both ideas.

The notebook pipeline is fixed and worth memorizing:

| Step | Call | Why this order |
| --- | --- | --- |
| 1. Generate data | `make_moons(n_samples=600, noise=0.25)` | A nonlinear problem with known structure |
| 2. Split | `train_test_split(..., stratify=y)` | Test points never influence fitting |
| 3. Scale | `StandardScaler().fit(X_train)` | Equal treatment of features; fitted on train only |
| 4. Fit | `MLPClassifier(hidden_layer_sizes=(16, 8))` | Weights learned from training data |
| 5. Evaluate | `accuracy_score(y_test, ...)` | One number on unseen data |

Scaling matters because an unscaled feature with a range of 100 dominates the
first gradient steps and can stall training. The **decision-boundary plot**
evaluates the model on a dense grid: a curved region means the network learned an
interaction, and a boundary that snakes around single points means it learned the
noise. With `noise=0.25`, some test points are genuinely on the wrong side of the
true boundary, so 1.00 would be suspicious rather than impressive.

### 7. What 0.94 does and does not tell you

| Claim | Supported by the notebook? | Why |
| --- | --- | --- |
| The MLP beats logistic regression on this split | Yes | 0.94 vs 0.86 on the same 150 test points |
| The MLP will beat logistic regression on new sensor data | Not yet | One split of one synthetic dataset |
| The MLP is well calibrated | No evidence | Accuracy says nothing about probability quality |
| The improvement is stable | Not measured | No seed variation, no confidence interval |
| The model is safe to deploy | No | No baseline beyond logistic, no error analysis |

A test set of 150 balanced points has real sampling noise; a few flipped points
move accuracy by several percentage points. Report the split, the seed, and the
test size along with the number.

## Guided walkthrough

The [guided notebook](notebook.md) is the practical half of this lesson. It runs
in six short sections:

1. **Perceptron** - builds OR, then shows the same unit failing on XOR.
2. **Hidden layer** - constructs XOR from OR and AND, proving that two hidden
   units are sufficient.
3. **Activations** - plots ReLU, sigmoid, and tanh and saves
   `outputs/f11_activations.png`.
4. **Nonlinear classification** - trains logistic regression and an MLP on the
   same two-moons split, prints 0.86 and 0.94, and asserts that the MLP is
   better.
5. **Shapes** - prints `(2, 16)`, `(16, 8)`, `(8, 1)` and 193 parameters.
6. **Decision boundary** - evaluates the MLP on a grid and saves
   `outputs/f11_decision_boundary.png`.

Each assertion is a claim you can check: OR equals `[0, 1, 1, 1]`, the
single-unit XOR output differs from `[0, 1, 1, 0]`, the two-layer output equals
it, and the MLP beats logistic regression. Sections 1-3 prove the geometry and
the hand-built construction; sections 4-6 prove that a trained network exploits
the same idea on data it has not memorized. If an assertion fails, the explanation
above tells you which idea to revisit before changing code.

## Practical exercise

This exercise stays inside the notebook's two-moons experiment. It is not the
independent lab.

1. Run the notebook once unchanged and record the MLP accuracy, the parameter
   count, and the two figure paths.
2. Change only `hidden_layer_sizes` to `(8,)`, rerun the model and shape cells,
   and record accuracy and parameters (expected: 33 parameters).
3. Change only `hidden_layer_sizes` to `(64, 64)`, rerun, and record accuracy and
   parameters (expected: 4417 parameters).
4. Compare the three decision-boundary plots. Then restore `(16, 8)`.

Expected observations:

| Configuration | Parameters | Accuracy you should expect | Boundary |
| --- | --- | --- | --- |
| `(8,)` | 33 | Near the logistic baseline, possibly lower | Nearly straight or simple curve |
| `(16, 8)` | 193 | About 0.94 | Smooth curve following the crescents |
| `(64, 64)` | 4417 | 0.93-0.96, not automatically higher | Rougher, may wrap around single points |

If the largest model is not the most accurate, that is the lesson: capacity buys
the ability to fit, not a guarantee of better generalization. Write one sentence
explaining the result you observed.

## Common mistakes and how to diagnose them

| Symptom | Likely cause | How to diagnose | Fix |
| --- | --- | --- | --- |
| MLP accuracy is near 0.5 or below logistic | Features unscaled, or the model never converged | Print `scaler.mean_` and check the `ConvergenceWarning` | Scale inside the pipeline; raise `max_iter` |
| MLP output is identical to logistic regression | Activation removed or set to `"identity"` | Print `mlp.activation` and the weight shapes | Use `relu`, `tanh`, or `logistic` |
| Assertion on XOR fails | Weights or bias changed accidentally | Print the four outputs and the target | Restore `bias=-0.5` and the OR/AND offsets |
| Parameter count does not match your arithmetic | Confusing units with parameters, or a layer shape changed | Print every `coefs_` and `intercepts_` shape | Sum `w.size + b.size` per layer |
| Accuracy changes every rerun | `random_state` removed, or cells run out of order | Restart the kernel and run all cells | Keep `SEED = 42` and a clean top-to-bottom run |
| Boundary plot is a single color | Grid transformed with the wrong scaler, or model predicts one class | Print the unique values of `zz` | Transform the grid with the same fitted scaler |
| `ConvergenceWarning` but accuracy looks fine | Iteration limit reached before the tolerance | Compare 2000 with 5000 iterations | Raise `max_iter` or scale the data |
| Training accuracy is high, test accuracy is low | Overfitting, usually with a large architecture and little data | Compare train and test accuracy | Reduce width, add regularization, collect more data |

## Checkpoint

- [ ] I can write the OR weights and bias from memory and justify each value.
- [ ] I can explain, without the notebook, why XOR has no linear separator.
- [ ] I can draw the two-hidden-unit XOR construction and label OR and AND.
- [ ] I can compute the parameter count of `(2, 16)`, `(16, 8)`, `(8, 1)` by hand.
- [ ] I can say what a ReLU does and what a dead ReLU is.
- [ ] I ran the notebook from a clean kernel and both figures exist.
- [ ] I can state one reason 0.94 is not proof of deployment readiness.

## Next step

1. Run the [guided notebook](notebook.md) and check your outputs against the
   expected-results table.
2. Complete the [lab brief](lab.md): train a network on noisy XOR and explain
   which hidden width is enough.
3. Score your evidence with the [assessment](assessment.md).
4. Continue to [F12 - Backpropagation](../f12-backpropagation/index.md) to see
   how these weights are actually learned.

The module plan for this material is
[M03 - Deep learning foundations](../../syllabus/level-1-foundations.md#m03).

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
