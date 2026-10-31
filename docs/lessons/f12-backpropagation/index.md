# F12 - Tensors, gradients, loss functions, and backpropagation {#f12}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Foundations (implements [M03](../../syllabus/level-1-foundations.md#m03)) |
| **Study time** | 12 hours: 3 h theory, 5 h guided notebook, 3 h lab, 1 h assessment |
| **Hardware** | CPU or GPU. The core runs on CPU in under a minute; a GPU is optional. |
| **Prerequisites** | [F11 - Neural network fundamentals](../f11-neural-networks/index.md); derivative as a slope; the chain rule; matrix multiplication |
| **You will produce** | An executed PyTorch notebook, a gradient check, a training-curve diagnosis, an independent lab report, and a short reflection |

## Why this module exists

A team trains a small classifier and watches two numbers:

| Epoch | Train loss | Validation loss | Validation accuracy |
| --- | --- | --- | --- |
| 50 | 0.146 | 0.153 | 0.950 |
| 100 | 0.128 | 0.161 | 0.945 |
| 150 | 0.124 | 0.173 | 0.945 |
| 200 | 0.121 | **0.177** | 0.945 |

Training loss keeps falling. Validation loss turns upward after roughly epoch 50.
The team's instinct is to train longer, which makes the gap worse. Their problem
is not effort. They have no model of what each number measures, so they cannot
tell improvement from memorization.

This module supplies that model. You will see how a **tensor** carries data and
device information, how the **forward pass** composes layers, how a **loss
function** turns predictions into one number, how **autograd** computes
derivatives through the chain rule, and how an **optimizer** uses those
derivatives. Then the curves above become readable rather than mysterious.

!!! note "Scope"
    You will not implement a full framework. You will compute a derivative by
    hand, verify PyTorch's autograd against a finite difference, and train a
    337-parameter network. The goal is to trust the tools because you can check
    them, not because they are popular.

## Learning objectives

By the end of this module, you can:

1. Create a tensor, state its shape, dtype, and device, and predict the shape of
   an operation involving broadcasting.
2. Compute a derivative by hand and confirm it with `torch.autograd`.
3. Verify an analytic gradient against a central finite difference and explain
   why the two never match exactly.
4. Explain what `BCEWithLogitsLoss` computes and why it is preferred over
   sigmoid followed by `BCELoss`.
5. Count the trainable parameters of a small `nn.Sequential` model from its layer
   sizes.
6. Describe one full training step: forward pass, loss, `backward()`, optimizer
   step, and gradient reset.
7. Diagnose underfitting and overfitting from training and validation curves, and
   name the change you would test next.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| F11 completed | You need the idea of a hidden layer and an activation |
| PyTorch installed (`requirements/cpu.txt` or `requirements/gpu.txt`) | The notebook imports `torch` and will not run without it |
| Ability to read a derivative such as `d(x^2)/dx = 2x` | Autograd is checked against hand calculation |
| Matrix multiplication shapes | Most tensor bugs are shape bugs |
| About 1 GB free disk and 5 minutes of CPU time | Model and figures are small |

A GPU is optional. The notebook selects CUDA only when it is available and
otherwise runs on CPU with identical code.

## The concepts you need

### 1. Tensors: shape, dtype, device, and broadcasting

A **tensor** is an n-dimensional array with three extra facts attached: a
**dtype** (such as `float32`), a **device** (`cpu` or `cuda:0`), and whether it
tracks gradients (`requires_grad`). PyTorch operations require matching devices;
a CPU tensor and a GPU tensor cannot be added directly.

**Broadcasting** lets operations combine tensors of different but compatible
shapes. The notebook shows both behaviors:

```python
a = torch.tensor([[1.0, 2.0], [3.0, 4.0]])   # (2, 2)
b = torch.tensor([10.0, 20.0])               # (2,)
a + b        # (2, 2): b is added to every row
a @ b        # (2,):   matrix-vector product
```

| Expression | Left shape | Right shape | Result shape | Rule used |
| --- | --- | --- | --- | --- |
| `a + b` | `(2, 2)` | `(2,)` | `(2, 2)` | `b` broadcast across rows |
| `a @ b` | `(2, 2)` | `(2,)` | `(2,)` | Matrix times vector |
| `batch @ weights` | `(8, 3)` | `(3, 4)` | `(8, 4)` | Inner dimensions match |
| `(8, 3) @ (4, 3)` | `(8, 3)` | `(4, 3)` | error | Inner dimensions 3 and 4 disagree |

Broadcasting is convenient and dangerous: a wrong but compatible shape produces
a plausible result instead of an error. Print shapes before and after every
operation that changes them.

### 2. The forward pass composes layers

A **forward pass** pushes a batch through the model and produces predictions. A
`nn.Linear(2, 16)` computes `X @ W.T + b`; a `nn.ReLU()` applies `max(0, z)`
elementwise. Stacking them gives a **multilayer perceptron** (MLP).

```python
model = nn.Sequential(
    nn.Linear(2, 16), nn.ReLU(),
    nn.Linear(16, 16), nn.ReLU(),
    nn.Linear(16, 1),
)
```

The final layer returns one **logit** per row: an unbounded score, not a
probability. Keeping scores as logits is deliberate; the loss function applies
the sigmoid internally in a numerically stable way.

### 3. Loss functions turn predictions into one number

A **loss function** measures the disagreement between predictions and targets.
Training minimizes its average over the batch.

| Loss | Formula, per example | Output layer | Use when |
| --- | --- | --- | --- |
| Mean squared error | `(prediction - target)^2` | Linear | Regression |
| Binary cross-entropy | `-[y*log(p) + (1-y)*log(1-p)]` | Sigmoid probability | Two classes |
| `BCEWithLogitsLoss` | Sigmoid and BCE fused, computed in log space | Raw logit | Two classes, default choice |
| Cross-entropy | Softmax and negative log-likelihood fused | Raw logits | More than two classes |

Applying `sigmoid` yourself and then `BCELoss` can overflow or underflow for
large logits. `BCEWithLogitsLoss` avoids that and is what the notebook uses.

### 4. Gradients, the chain rule, and autograd

A **gradient** is the vector of partial derivatives of the loss with respect to
each parameter. It points in the direction of steepest increase; training steps
in the opposite direction.

For `y = x^2 + 3x`, the derivative is `2x + 3`, which equals **7** at `x = 2`.
PyTorch confirms it:

```python
x = torch.tensor(2.0, requires_grad=True)
y = x**2 + 3 * x
y.backward()
print(x.grad.item())   # 7.0
```

**Autograd** records every operation on tensors that require gradients, building
a graph. `backward()` walks that graph in reverse and applies the chain rule. Two
consequences matter in practice:

- Gradients **accumulate** in `.grad`. Call `optimizer.zero_grad()` before each
  backward pass or you silently add yesterday's gradient to today's.
- The graph is freed after `backward()` unless you pass `retain_graph=True`.
  Calling `backward()` twice on the same graph without it raises an error.

### 5. Backpropagation, layer by layer

**Backpropagation** is the chain rule applied layer by layer. For each layer, the
forward pass keeps the input and output. The loss produces a gradient with
respect to its input. Each layer then multiplies by its local derivative,
accumulates the gradient for its weights, and passes a gradient to the layer
before it.

| Quantity | Shape | Meaning |
| --- | --- | --- |
| `X` | `(n, 2)` | Input batch, `n = 600` in the notebook |
| `W1`, `b1` | `(2, 16)`, `(16,)` | First linear layer |
| `H1` | `(n, 16)` | First hidden activations |
| `W2`, `b2` | `(16, 16)`, `(16,)` | Second linear layer |
| `H2` | `(n, 16)` | Second hidden activations |
| `W3`, `b3` | `(16, 1)`, `(1,)` | Output logits |
| `loss` | scalar | Mean binary cross-entropy |

Parameter count:

| Layer | Arithmetic | Parameters |
| --- | --- | --- |
| `Linear(2, 16)` | `2*16 + 16` | 48 |
| `Linear(16, 16)` | `16*16 + 16` | 272 |
| `Linear(16, 1)` | `16*1 + 1` | 17 |
| **Total** | | **337** |

### 6. Optimizers and the learning rate

An **optimizer** uses gradients to update parameters. The **learning rate** is
the step size.

| Optimizer | Idea | Typical use | Main risk |
| --- | --- | --- | --- |
| SGD | Step opposite the gradient, scaled by learning rate | Simple baselines, fine-tuning | Slow on badly scaled problems |
| SGD with momentum | Accumulate a velocity to push through flat regions | Vision training | Momentum too high overshoots |
| Adam | Per-parameter adaptive step from first and second moment estimates | Default for small networks and quick experiments | Can generalize slightly worse; still needs a tuned learning rate |

The notebook uses `Adam(lr=0.03)` for 200 epochs. Learning rate symptoms are
easy to recognize: loss barely moves (too low), loss oscillates or becomes `NaN`
(too high), loss falls then jumps (borderline).

### 7. Gradient checks and reading two curves

A **finite difference** estimates a derivative by perturbing the input:

```text
numeric = (loss(w + eps) - loss(w - eps)) / (2 * eps)
```

The notebook computes the analytic gradient of a mean-squared-error loss with
respect to `w` and compares it with the numeric estimate. They agree to about
`5e-5`, not exactly, because a finite difference approximates a limit. Too large
an `eps` adds truncation error; too small an `eps` adds floating-point noise.

Once gradients are trustworthy, the curves are the main diagnostic:

| Pattern | Reading | Next change to test |
| --- | --- | --- |
| Train and validation loss both high and flat | Underfitting | Wider layers, longer training, better features |
| Train loss falls, validation loss falls then rises | Overfitting | Early stopping, weight decay, smaller model, more data |
| Train loss falls, validation loss flat from the start | Model not learning generalizable structure | Check labels, leakage, and split |
| Loss becomes `NaN` | Learning rate too high or unstable loss | Lower the learning rate, check input scaling |
| Validation accuracy high but loss rising | Confidence growing on wrong examples | Track accuracy and loss together |

In the notebook, validation loss is lowest near epoch 50 and rises to 0.177 by
epoch 200 while training loss falls from 0.146 to 0.121. Validation accuracy stays
at 0.945, so the model is not becoming less accurate; it is becoming more
confident and slightly more wrong. That is the overfitting signature this module
teaches you to name.

## Guided walkthrough

The [guided notebook](notebook.md) runs these sections:

1. **Tensors** - shape, dtype, broadcasting, and a matrix multiplication.
2. **Autograd** - `dy/dx = 7.0` at `x = 2`.
3. **Gradient check** - analytic `-0.346939` against numeric `-0.346988`.
4. **Model, loss, optimizer** - a 337-parameter MLP, `BCEWithLogitsLoss`, Adam.
5. **Training** - 200 epochs, checkpoints every 10, final train 0.948 and
   validation 0.945.
6. **Curves** - loss and accuracy plots saved to
   `outputs/f12_training_curves.png`, plus a shape table for backpropagation.

What each part proves: sections 1-3 prove that the mechanics are correct on cases
you can verify by hand; sections 4-6 prove that the same mechanics scale to a
model whose answer you cannot compute by hand. If sections 1-3 pass but the
curves look wrong, the problem is in data or training configuration, not in
autograd.

## Practical exercise

This exercise stays inside the notebook and is not the independent lab.

1. Run the notebook unchanged, then record final train and validation accuracy
   and the epoch where validation loss is lowest.
2. Replace both `nn.ReLU()` layers with `nn.Identity()` and retrain. Keep the
   seed, optimizer, learning rate, and epochs fixed.
3. Record the parameter count (it does not change), the final accuracies, and the
   shape of the learned decision region.
4. Restore the ReLU layers and confirm the original result.

Expected observations:

| Configuration | Parameters | Validation accuracy | Boundary |
| --- | --- | --- | --- |
| Two ReLU layers | 337 | About 0.945 | Curved, follows the crescents |
| ReLU replaced by Identity | 337 | Around 0.86-0.89, close to logistic regression | A straight line |

The parameter count is unchanged because `Identity` adds no parameters. The
accuracy drop is the point: without a nonlinearity, the three linear layers
compose into one linear map, so depth buys nothing. Write two sentences
explaining why the same number of weights performs worse.

## Common mistakes and how to diagnose them

| Symptom | Likely cause | How to diagnose | Fix |
| --- | --- | --- | --- |
| Loss does not decrease at all | Missing `optimizer.zero_grad()` or learning rate far too low | Print `loss.item()` each epoch; check the optimizer block | Reset gradients each step; raise the learning rate |
| Loss becomes `NaN` | Learning rate too high, or unscaled inputs | Lower the learning rate by 10x and rerun | Scale features; reduce learning rate |
| `RuntimeError: mat1 and mat2 shapes cannot be multiplied` | Layer sizes do not chain | Print each layer's in/out features | Match adjacent layer sizes |
| `RuntimeError: expected scalar type Float but found Double` | NumPy `float64` converted without casting | Print `X.dtype` and `y.dtype` | Cast arrays to `float32` before `torch.tensor` |
| BCE loss is wrong or negative | Sigmoid applied before `BCEWithLogitsLoss`, or targets shaped `(n,)` | Check the output shape and target shape | Use raw logits and targets shaped `(n, 1)` |
| Validation loss rises while train loss falls | Overfitting | Compare curves at the same checkpoint | Add early stopping, weight decay, or more data |
| `x.grad` is `None` | `requires_grad` missing, or the graph was freed | Check `x.requires_grad` before `backward()` | Set `requires_grad=True`; do not call `backward()` twice |
| Gradient check disagrees by a large margin | `eps` too large or too small, or the loss uses a different batch | Print both values and try `eps=1e-4` and `1e-5` | Use central differences with a moderate `eps` |
| Accuracy is suspiciously perfect | Evaluate on training data, or test leakage | Print which split produced the number | Evaluate on the held-out split only |

## Checkpoint

- [ ] I can explain the difference between a logit and a probability.
- [ ] I can compute `dy/dx` for `y = x^2 + 3x` at any point and check it in PyTorch.
- [ ] I can explain why `optimizer.zero_grad()` is required.
- [ ] I can derive 337 parameters for `(2, 16)`, `(16, 16)`, `(16, 1)`.
- [ ] I can describe one full training step in the correct order.
- [ ] I can read a train/validation curve and name underfitting or overfitting.
- [ ] I ran the notebook and the curve figure exists.

## Next step

1. Run the [guided notebook](notebook.md) and compare against the expected
   results.
2. Complete the [lab brief](lab.md): train on a new dataset and justify an
   early-stopping decision from the curves.
3. Score your evidence with the [assessment](assessment.md).
4. Continue to [F13 - Reproducibility](../f13-reproducibility/index.md) to make
   these runs repeatable and comparable.

The module plan is [M03 - Deep learning foundations](../../syllabus/level-1-foundations.md#m03).

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
