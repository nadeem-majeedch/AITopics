# CV06 - Transfer learning with pretrained vision models {#cv06}

**Section path:** [Overview](index.md) · **Module 6** · [Lab 3](labs/lab3-scratch-vs-transfer.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only for the section's backbone; a GPU is optional for real ImageNet weights |
| **Prerequisites** | CV05, and a working notion of what a pretrained model is (CA09 covers the same idea for text) |
| **You will produce** | Three conditions measured on the same split, a parameter-budget table, and a judgement about when the comparison transfers to real photos |

## Why this module exists

In practice you almost never train a vision model from scratch. You take a network
trained on millions of images, replace the last layer, and train that. The claim is that
the early layers learned generic features - edges, textures, colour blobs - that transfer
to your task.

The claim is usually true and always conditional. This module measures it on data small
enough to run in ten seconds, and is explicit about what the measurement does *not* prove.

## Three conditions, not two

| Condition | What trains | Params trainable | Test accuracy | Time |
| --- | --- | --- | --- | --- |
| From scratch | whole network, random init | 72,564 | 0.500 | 0.5 s |
| Frozen features + linear probe | one linear layer on frozen embeddings | 260 | 0.500 | 0.1 s |
| Last block fine-tuned | trunk frozen except the final block | 55,812 | **0.722** | 0.1 s |

Measured on the four-class "everyday objects" set (84 train / 18 val / 18 test), 20
epochs per condition, identical split and seed.

Read the middle row carefully: **260 parameters match 72,564**. If the features are
good, the head is almost free. That is the economic argument for transfer learning, and
it is visible in one number.

Read the third row carefully too: fine-tuning beats both, but the linear probe alone
does not. On this data the frozen features are not linearly separable enough for a
one-layer head. A single "transfer learning helps" claim would have hidden that.

## What "pretrained" means here, exactly

!!! warning "This backbone is not ImageNet"
    Downloading torchvision weights is not available in this environment. The section
    therefore trains its own **offline backbone**: a `TinyCNN` trained for 20 epochs on
    the synthetic shape set, reaching **0.976** validation accuracy on that task. It is
    then frozen and reused as if it were pretrained.

    That is a legitimate *methodology* demonstration - the mechanics are identical - but
    it is not evidence about ImageNet-scale features. The code path for real weights
    exists (`transfer.torchvision_backbone`), and it reports its own failure rather than
    pretending to work.

```python
backbone, history = transfer.build_pretrained_backbone(epochs=20)   # 0.976 val on shapes
probe = transfer.train_linear_probe(backbone, objects)
finetuned = transfer.train_partial_finetune(backbone, objects)
```

## Freezing, and what actually moves

```python
transfer.freeze_trunk(backbone)          # requires_grad = False everywhere
transfer.unfreeze_last_block(backbone)   # the last block only
```

Three details that decide whether this works:

1. **Frozen BatchNorm still updates running statistics** unless you call `.eval()`. A
   "frozen" backbone in train mode is not frozen; its normalization drifts.
2. **Optimizer created before freezing** keeps parameters you thought were excluded.
   Freeze first, then build the optimizer.
3. **Learning rate differs by group.** Fine-tuning a pretrained block wants 10-100x
   smaller lr than a randomly initialised head. One lr for both either destroys the
   features or never trains the head.

```python
optimizer = torch.optim.Adam([
    {"params": trunk_params, "lr": 1e-4},
    {"params": head_params,  "lr": 2e-3},
])
```

## Domain gap is the whole story

Transfer works when source and target share low-level structure. It fails when they do
not, and no amount of fine-tuning recovers information the source never had.

| Source -> target | Expected outcome |
| --- | --- |
| Natural photos -> natural photos (different classes) | strong transfer |
| Natural photos -> medical slides | weak; features are the wrong statistics |
| Natural photos -> depth maps or sketches | weak to moderate |
| Synthetic shapes -> synthetic objects | moderate; measured here |
| Any -> your 40 images of one product | fine-tuning still wins, but watch overfitting |

The last row is the honest caveat for small datasets: with 40 images, a 55,812-parameter
fine-tune can memorise. Watch the validation gap, not the training loss.

## How to report a transfer result

Never report a single accuracy. Report the triple:

```text
condition            test_acc   trainable_params   train_seconds
scratch              0.500      72,564             0.5
linear probe         0.500      260                0.1
last block ft        0.722      55,812             0.1
```

Then answer: *is the gain worth the parameters?* If a 260-parameter probe matches
scratch, the answer for deployment is yes regardless of which number is higher, because
the probe is 280x smaller and trains instantly.

## Practice

1. Reproduce the three conditions. Confirm the parameter counts with
   `count_parameters`.
2. Freeze the trunk but forget `model.eval()` during the probe. Report whether the
   result changes, and explain why it can.
3. Fine-tune only the classifier versus the last block. Report both accuracies and the
   trainable-parameter counts.
4. Write two sentences on what this experiment does *not* tell you about ImageNet
   transfer.

## Check yourself

1. Why can a 260-parameter head match a 72,564-parameter network on the same split?
2. You freeze the trunk, then create the optimizer. Why is the order a bug risk?
3. Name a source/target pair where you would expect transfer to fail, and say what
   evidence would change your mind.

## What comes next

[CV07](cv07-fine-tuning.md) turns the partial fine-tune into a procedure: layer groups,
differential learning rates, discriminative schedules, and when to stop.
