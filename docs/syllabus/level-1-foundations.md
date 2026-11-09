# Level 1 - Foundations

**Modules:** M02-M05 | **Hours:** 64 | **Hardware:** CPU-only to GPU recommended

Level 1 builds the skills that every later module assumes: formulating a learning
problem, training and diagnosing models, running controlled experiments, and
preparing data that you can defend.

!!! note "Level outcome"
    You can train and evaluate a classical model and a deep model, explain their
    errors with evidence, and produce a documented dataset and model card.

## Readiness check

- Can you split data without leakage and explain why a test set exists?
- Can you write a PyTorch training loop and debug tensor shapes?
- Can you compute and interpret precision, recall, and F1?
- Have you ever documented a dataset's source, license, and limitations?

If most answers are no, start at M02. If all are yes, use the labs as placement
evidence before skipping modules.

---

## M02 - Machine learning foundations {#m02}

**Published material:** [F03-F10 lesson sequence](../lessons/f03-numpy-pandas/index.md).

!!! success "Published as the F03-F10 sequence"
    This module is delivered by [F03](../lessons/f03-numpy-pandas/index.md)
    through [F10](../lessons/f10-metrics-validation/index.md). Those units use
    small synthetic CC0 tables instead of California Housing, and they add
    independent labs and assessments. The outcomes, leakage discipline, metric
    selection, and pipeline requirements below remain the authoritative scope.

**Level 1 | 16 hours | CPU-only | Prerequisite: M01**

### Learning objectives

By the end of this module, you can:

1. Formulate a supervised learning problem with a clear target and decision use.
2. Create train, validation, and test splits without leakage.
3. Build a credible baseline before trying complex models.
4. Train and compare linear models, tree ensembles, and gradient boosting.
5. Choose metrics that match the task, including precision, recall, F1, ROC-AUC,
   PR-AUC, MAE, and RMSE.
6. Evaluate calibration and performance on important data slices.
7. Package preprocessing and modeling in a reproducible scikit-learn pipeline.

### Prerequisites

- M01.
- Basic statistics: mean, variance, distributions, sampling.
- Basic linear algebra: vectors and matrix multiplication.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 4 h | 6 h | 5 h | 1 h | 16 h |

### Required theory

- Supervised vs unsupervised learning; regression vs classification.
- Features, labels, loss functions, and the i.i.d. assumption.
- Bias-variance trade-off, overfitting, and regularization.
- Data leakage: target leakage, duplicate leakage, and temporal leakage.
- Baselines: mean, majority class, and a simple heuristic.
- Linear and logistic regression; decision trees; random forests; gradient
  boosting.
- Confusion matrix, precision, recall, F1, ROC-AUC, PR-AUC, MAE, RMSE, R-squared.
- Probability calibration and why accuracy alone misleads.
- Cross-validation, model selection, and nested evaluation.
- Class imbalance and threshold selection.
- Fairness slices and the limits of aggregate metrics.
- Reproducible pipelines with `Pipeline` and `ColumnTransformer`.

### Guided notebook

**Implemented path:** the module is split across eight foundation notebooks.

| Unit | Notebook | Focus |
| --- | --- | --- |
| F03 | `notebooks/foundations/f03_numpy_pandas.ipynb` | Arrays, pandas tables, grouping, merging |
| F04 | `notebooks/foundations/f04_data_cleaning.ipynb` | Missing values, categories, preprocessing pipeline |
| F05 | `notebooks/foundations/f05_splits.ipynb` | Train/validation/test, groups, leakage |
| F06 | `notebooks/foundations/f06_eda.ipynb` | Distributions, correlation, outliers |
| F07 | `notebooks/foundations/f07_supervised_unsupervised.ipynb` | Clustering, PCA, supervised comparison |
| F08 | `notebooks/foundations/f08_regression_classification.ipynb` | Baselines, linear/ridge, logistic, metrics |
| F09 | `notebooks/foundations/f09_tree_ensembles.ipynb` | Trees, forests, boosting, cross-validation |
| F10 | `notebooks/foundations/f10_metrics_validation.ipynb` | Imbalance, thresholds, overfitting, leakage |

Together they cover EDA, leakage checks, splits, baselines, linear and tree
models, task-appropriate metrics, threshold selection, and a reusable
preprocessing pipeline. The published sequence uses small synthetic CC0 tables
instead of the California Housing fetcher, so it runs offline and has no
redistribution ambiguity.

**Hardware:** CPU-only.

### Independent lab

**Brief:** Build an end-to-end tabular model for a dataset you have not used in
the guided notebook. The published [F08 lab](../lessons/f08-regression-classification/lab.md)
uses the synthetic house-price table. California Housing, UCI Adult, Wine
Quality, Bank Marketing, or another public dataset are acceptable alternatives
with instructor approval.

Required evidence:

- Problem statement and decision use.
- Dataset card with provenance, license, and limitations.
- Leakage audit.
- Baseline and at least two stronger models.
- Cross-validation and a held-out test set.
- Task-appropriate metrics with confidence intervals or repeated splits.
- Calibration analysis for classification, or residual analysis for regression.
- At least three data slices with interpretation.
- A model card and a two-page report.

**Constraints:** No target leakage. No tuning on the test set. CPU-only. The
notebook must run from a clean kernel.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- A baseline is present and correctly computed.
- The test set is untouched until final evaluation.
- Metrics match the problem and class balance.
- At least one fairness or slice-based analysis is included.

### Deliverables

- Executed notebook.
- Two-page lab report.
- Dataset card and model card.
- Reflection on model choice and error patterns.

### Next step

M03 - Deep learning foundations.

### Risks and notes

- **Leakage is the most common failure.** Check duplicates across splits and
  confirm that preprocessing is fit only on training data.
- **Accuracy is misleading** on imbalanced data. Report precision, recall, and
  PR-AUC.
- **Do not chase leaderboard scores.** A well-explained baseline is stronger
  evidence than an unexplained ensemble.

---

## M03 - Deep learning foundations {#m03}

**Published material:** [F11-F13 lesson sequence](../lessons/f11-neural-networks/index.md).

!!! success "Published as the F11-F13 sequence"
    This module is delivered by [F11](../lessons/f11-neural-networks/index.md)
    through [F13](../lessons/f13-reproducibility/index.md). Those units use small
    synthetic data and compact PyTorch models rather than Fashion-MNIST, so every
    core exercise runs on a laptop CPU. The outcomes below remain the
    authoritative scope; device comparison is optional and was not executed on a
    GPU during authoring.

**Level 1 | 16 hours | CPU or GPU | Prerequisite: M02**

### Learning objectives

By the end of this module, you can:

1. Explain tensors, shapes, broadcasting, and automatic differentiation.
2. Implement a small neural network forward and backward pass in NumPy.
3. Build the equivalent model in PyTorch with a clean training loop.
4. Diagnose underfitting, overfitting, exploding gradients, and dead units.
5. Use activation functions, initialization, dropout, and normalization
   appropriately.
6. Compare optimizers and learning-rate schedules with controlled experiments.
7. Move computation between CPU and GPU safely and measure the difference.

### Prerequisites

- M02.
- Basic calculus: derivative as a slope; chain rule intuition.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 4 h | 6 h | 5 h | 1 h | 16 h |

### Required theory

- Perceptrons, multilayer networks, and universal approximation intuition.
- Forward pass, loss, gradients, and backpropagation.
- Tensors, shapes, broadcasting, and matrix multiplication.
- Activation functions and the dying-ReLU problem.
- Weight initialization and vanishing/exploding gradients.
- SGD, momentum, Adam, and learning-rate schedules.
- Regularization: weight decay, dropout, early stopping.
- Batch normalization and layer normalization.
- PyTorch `Dataset`, `DataLoader`, `nn.Module`, `optimizer`, and `autograd`.
- Device management and deterministic behavior.

### Guided notebook

**Implemented path:** the module is split across three foundation notebooks.

| Unit | Notebook | Focus |
| --- | --- | --- |
| F11 | `notebooks/foundations/f11_neural_networks.ipynb` | Perceptrons, hidden layers, activations, MLP |
| F12 | `notebooks/foundations/f12_backpropagation.ipynb` | Tensors, autograd, loss, optimizer, training curves |
| F13 | `notebooks/foundations/f13_reproducibility.ipynb` | Seeds, determinism, timing, run tracking |

Together they implement a manual NumPy network, a numerical gradient check, a
PyTorch training loop with train/validation curves, a CPU timing comparison, and
a JSONL run log. The published sequence uses two-dimensional synthetic data and a
small tabular classification task instead of Fashion-MNIST, so every core
exercise runs on a laptop CPU.

**Hardware:** CPU works for the complete sequence; a GPU comparison is optional
and was not executed during authoring.

### Independent lab

**Brief:** Run a controlled ablation study on a small neural network. The
published [F12 lab](../lessons/f12-backpropagation/lab.md) uses a synthetic
tabular dataset; Fashion-MNIST or a comparable public dataset is acceptable with
instructor approval and a larger compute budget.

- Fix the data split, seed, and evaluation protocol.
- Compare at least four configurations: optimizer, learning rate, dropout,
  initialization, or batch size.
- Report mean and spread across at least three seeds.
- Include training curves and a table of final metrics.
- Explain at least two surprising results.
- Keep the total compute budget under the stated limit (for example 30 GPU
  minutes or 45 CPU minutes).

**Constraints:** No test-set tuning. No hidden early stopping differences
between runs. Record hardware and runtime.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- Backpropagation is implemented or clearly explained.
- The ablation changes one factor at a time.
- Results include multiple seeds, not one lucky run.
- Curves are interpreted, not just plotted.

### Deliverables

- Executed notebook with NumPy and PyTorch implementations.
- Ablation table with seeds and runtime.
- Short report explaining the results.
- Reflection on debugging experience.

### Next step

M04 - Training models from scratch.

### Risks and notes

- **GPU memory errors:** reduce batch size first, then model width.
- **Non-determinism:** some GPU operations are not bitwise deterministic; report
  variance rather than claiming exact reproducibility.
- **Notebook state:** restart the kernel before final runs.

---

## M04 - Training models from scratch {#m04}

**Published material:** [Model training overview](../lessons/model-training/index.md).

**Level 1 | 18 hours | GPU recommended | Prerequisite: M03**

### Learning objectives

By the end of this module, you can:

1. Explain convolution, pooling, receptive fields, and feature hierarchies.
2. Implement a convolutional network training pipeline from scratch.
3. Apply augmentation, regularization, and learning-rate scheduling deliberately.
4. Track experiments with reproducible logs and compare runs.
5. Use mixed precision and checkpointing within a compute budget.
6. Evaluate a model with per-class metrics and error analysis.
7. Decide when training from scratch is justified versus transfer learning.

### Prerequisites

- M03.
- Comfort with PyTorch training loops and GPU/CPU device handling.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 4 h | 7 h | 6 h | 1 h | 18 h |

### Required theory

- Convolution, stride, padding, pooling, and receptive fields.
- Residual connections and the ResNet family.
- Data augmentation for images.
- Label smoothing and mixup (conceptual).
- Learning-rate schedules and warmup.
- Mixed-precision training and gradient clipping.
- Experiment tracking with TensorBoard or MLflow.
- Checkpointing, early stopping, and reproducibility.
- Compute budgeting and the cost of repeated runs.
- From-scratch vs transfer learning decision criteria.

### Guided notebook

**Notebook:** `notebooks/model-training/m04_training_from_scratch.ipynb`, executed
on Windows 11 CPU. The lesson sequence is
[MT01-MT05](../lessons/model-training/index.md).

The notebook trains a small CNN from scratch on 300 synthetic shape images. It
compares a random split with a grouped split and measures the near-duplicate
leakage, compares plain and augmented training, restores a checkpoint, times fp32
against bf16, and inspects per-class errors. The section index reports the measured
numbers.

**Dataset:** 300 shape images generated locally by `vision_core` under CC0-1.0.

**Hardware:** CPU-only (under a minute in the recorded run); a GPU is optional and
is not required for any measured result.

### Independent lab

**Brief:** Train an image classifier from scratch under a compute budget and
document the experiment.

Required evidence:

- Dataset card and augmentation policy.
- A fixed evaluation protocol and a simple baseline.
- At least three tracked experiments that test a hypothesis.
- Training curves, final metrics, per-class results, and confusion matrix.
- At least eight misclassified examples with analysis.
- A compute log: GPU type, batch size, epochs, wall-clock time, and peak VRAM.
- A recommendation: from scratch or transfer learning, with justification.

**Constraints:** Stay within the lab's compute budget. Do not use a pretrained
backbone. Do not tune on the test set.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- Experiments are tracked and comparable.
- The compute budget is respected and reported.
- Error analysis goes beyond a confusion matrix screenshot.
- The from-scratch vs transfer decision is justified with evidence.

### Deliverables

- Executed notebook.
- Experiment log with at least three runs.
- Evaluation report with error analysis.
- Short recommendation memo.

### Next step

M05 - Dataset preparation, labeling, cleaning, and augmentation.

### Risks and notes

- **Colab disconnects:** checkpoint every epoch to Drive or a local disk.
- **Augmentation leakage:** never augment the validation or test set.
- **Overfitting the test set:** use validation data for decisions.
- **Dataset licensing:** CIFAR-10 is widely used for research and education, but
  confirm terms before redistributing or deploying.

---

## M05 - Dataset preparation, labeling, cleaning, and augmentation {#m05}

**Published material:** [Model training overview](../lessons/model-training/index.md) - start with the dataset-audit modules and Lab 2.

**Level 1 | 14 hours | CPU-only | Prerequisite: M02-M04 (M03 minimum)**

### Learning objectives

By the end of this module, you can:

1. Design a dataset for a specific task and decision.
2. Write a labeling guideline that another person can follow consistently.
3. Measure inter-annotator agreement and diagnose ambiguous labels.
4. Find and remove duplicates, label errors, and train/test leakage.
5. Choose splits that respect time, groups, and domain boundaries.
6. Design an augmentation policy that preserves label semantics.
7. Document provenance, license, consent, bias, and limitations in a dataset
   card.

### Prerequisites

- M02 and M03. M04 is helpful but not required.
- Basic file handling and pandas.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 3 h | 5 h | 5 h | 1 h | 14 h |

### Required theory

- Data-centric AI and the cost of label noise.
- Sampling, stratification, and group-aware splits.
- Labeling guidelines, adjudication, and inter-annotator agreement.
- Cohen's kappa and percent agreement: what they do and do not measure.
- Duplicate detection and near-duplicate detection.
- Leakage: duplicates, groups, time, and preprocessing.
- Class imbalance and long-tailed data.
- Augmentation semantics for images, text, and audio.
- Privacy, consent, personal data, and sensitive attributes.
- Dataset licenses: CC, MIT, Apache, AGPL, research-only, and custom terms.
- Datasheets for datasets and dataset cards.
- Versioning data with manifests and checksums.

### Guided notebook

**Notebook:** `notebooks/model-training/m05_data_engineering.ipynb`, executed on
Windows 11 CPU. The lesson sequence is
[MT06-MT10](../lessons/model-training/index.md).

The notebook starts from 650 deliberately messy synthetic ticket rows and profiles
missing labels, duplicates, class balance, and near-duplicates. It builds a
group-aware split, measures overlap between splits, adds controlled label noise,
computes Cohen's kappa, and generates a dataset card from the cleaned data.

**Dataset:** synthetic support tickets generated locally under CC0-1.0; no
personal data.

**Hardware:** CPU-only.

### Independent lab

**Brief:** Create or curate a small dataset for a task in your chosen path.

- At least 100 items, with a written labeling guideline.
- Double-label at least 20 items and report agreement.
- Document provenance, license, collection method, and consent status.
- Perform a duplicate and leakage audit.
- Define train/validation/test splits and store a manifest.
- Write a dataset card and a one-page data statement.
- Identify at least two biases or coverage gaps.

**Constraints:** No personal or scraped data without explicit permission. No
copyrighted media beyond fair use or the license terms. Do not commit raw data
if the license forbids redistribution.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- The labeling guideline is usable by someone else.
- Agreement is measured, not assumed.
- The license and consent status are explicit.
- Splits prevent leakage by group, time, or duplicate.

### Deliverables

- Dataset card.
- Labeling guideline.
- Splits manifest with checksums.
- Agreement report.
- Data statement and bias analysis.

### Next step

M06 - Transformers and language models.

### Risks and notes

- **"Publicly available" is not a license.** Record the exact license and terms.
- **Sensitive attributes:** do not infer protected traits. If a dataset contains
  them, document their use and minimize access.
- **Augmentation can change labels.** Verify that transformed samples remain
  valid.
- **Small data is acceptable** if the limitations are documented and the
  evaluation is honest.

---

## Level 1 completion checklist

- [ ] I can frame a problem and choose metrics before modeling.
- [ ] I can build a leakage-free split and a credible baseline.
- [ ] I can write and debug a PyTorch training loop.
- [ ] I can run and interpret a controlled ablation.
- [ ] I can track experiments and report compute honestly.
- [ ] I can write a labeling guide and dataset card.
- [ ] I have portfolio artifacts for M02-M05.

Proceed to [Level 2 - Language AI](level-2-language.md).
