# Quiz bank - solutions

```markdown
**Assessments:** [Overview](../index.md) · [Solutions](index.md) · [Quiz bank](../quiz-bank.md)
```

One mark per question; a two-part question needs both parts. 4 = correct with the
mechanism, 3 = correct answer, 2 = partial, 1 = wrong. Chapter total out of 24.

---

## Chapter 1 - Data, cleaning, and splits

**1.1 - b.** Accuracy is 900/1,000 = 0.90 because 90% of rows are negative. Recall for
the positive class is 0/100 = 0 because no positive is ever predicted. This is the
canonical imbalance trap: the majority-class baseline looks respectable on accuracy
and is useless for the decision.

**1.2** Fitting the scaler on all rows lets the test set's mean and variance influence
training, so the test set is no longer unseen. The leak is small for a large sample and
can be large for a small one or when the test distribution differs. Correct order:
split first, fit on train, transform train and test with the train statistics. The same
rule applies to imputation, target encoding, feature selection, and PCA.

**1.3** The same customer appears in train and test, so the model can memorise
customer-specific patterns and the test score measures recall of customers rather than
generalisation to new ones. Use a group split by customer (for example
`GroupShuffleSplit` or `GroupKFold`), and check that the customer sets are disjoint.

**1.4** Missing at random: the missingness is unrelated to the outcome, for example a
sensor that drops readings at random; imputation is defensible. Missing because of the
outcome: the field is only filled when the customer churned, such as a cancellation
reason; the missingness itself encodes the label, so the model learns the recording
process. The second is leakage and the column must be dropped or reconstructed as it
would exist at prediction time.

**1.5** With a small dataset, 10% may be a handful of rows and may contain zero
positives, so recall and per-class metrics become undefined or wildly uncertain; model
selection on a 20-row validation set is noise. Better: a larger validation share with
cross-validation, or repeated stratified splits, and report intervals.

**1.6** Ask (a) what precision and recall are at the operating threshold, with the
confusion matrix and class counts, and (b) how the test set was constructed and whether
it is independent of training and of feature engineering. Also: what the model is
compared against, and what a false negative costs. A 99.2% accuracy on a 0.8% base rate
is consistent with a model that predicts "no fraud" for everything, which scores
99.2% and catches nothing.

---

## Chapter 2 - Classical machine learning

**2.1 - b.** Depth increases variance: the tree can carve the training set into small
regions that fit noise. Training error falls monotonically with depth while validation
error often rises after a point.

**2.2** Most likely: the out-of-bag estimate is being read as a test score, or the rows
are not independent (duplicates or group structure), or a feature encodes the target.
Check: count duplicate rows and groups; compare OOB with a held-out split by group; and
audit features for post-outcome availability. With 90 rows, any estimate is unstable
regardless.

**2.3** ROC AUC integrates over all thresholds and is insensitive to class balance. At
a fixed operating threshold, a model can rank positives above most negatives while
still producing many false positives, so precision (which depends on prevalence) is
low even though AUC is high. Precision-recall AUC or precision at the chosen threshold
is the honest view.

**2.4** (a) Overfitting: check learning curves and train-test gap. (b) Distribution
difference between validation and test: compare feature distributions and collection
dates. (c) Selection on the test set: audit how many times test was evaluated and
whether hyperparameters were chosen on it. (d) Small test set: compute a confidence
interval; a 0.19 difference on 40 rows may be noise.

**2.5** (a) Interpretability or regulatory requirement: coefficients and monotonicity
may be required, and a slightly higher score does not compensate. (b) The difference is
inside the confidence interval, so the simpler model is preferred on maintenance and
stability grounds. Also calibration, latency, and drift behaviour can favour the linear
model.

**2.6** A composite score hides incommensurable trade-offs (a millisecond is not a
point of accuracy), makes weights arbitrary, and lets a subgroup harm be averaged away.
Better: a decision framework with hard constraints (latency budget, minimum per-slice
recall, fairness gap ceiling), a small dashboard of separate metrics, and a stated
decision rule. Report the trade-off surface rather than one number.

---

## Chapter 3 - Neural networks and training

**3.1** Class 0 (logit 2.0). Softmax is monotone in the logits, so the largest logit
gets the largest probability; the exact value is about 0.62 given the other logits.

**3.2** Backpropagation computes the gradient of the loss with respect to every
parameter by applying the chain rule backwards through the computation graph. A
learning rate that is too large takes steps past the minimum, so the loss can
oscillate or diverge instead of decreasing.

**3.3** Overfitting. Interventions: early stopping at the best validation epoch;
regularisation (weight decay, dropout) or a smaller model; more data or augmentation;
reduce epochs or lower the learning rate with a schedule.

**3.4** Subtracting a constant `c` from every logit divides numerator and denominator
by `exp(c)`, so the ratio is unchanged: `exp(x-c)/Σexp(x-c) = exp(x)/Σexp(x)`.
Implementations do it because `exp(1000)` overflows to infinity, and the shifted
version stays in a safe range. The property is exact in real arithmetic and
approximately preserved in floating point, which is the point.

**3.5** (a) Weight initialisation: seed the initialiser and average over seeds.
(b) Data order and augmentation randomness: seed the loader and augmentation pipeline,
and fix the split. (c) Hardware nondeterminism and thread counts: enable deterministic
algorithms where possible, pin threads, and document what remains nondeterministic.
Report mean and spread over at least three seeds rather than a single run.

**3.6** Compare: task quality on a held-out set with a fixed rubric; cost per request
and per training run; latency and memory; context limits (400 examples may not fit, or
may crowd out instructions); data privacy and whether examples may be sent to the
larger model; update cadence and who maintains the adapter. Test the cheaper option
first because it is faster to iterate, and only move to the larger model if the smaller
one fails a stated threshold.

---

## Chapter 4 - Conversational AI and retrieval

**4.1 - b.** Chunking and retrieval decide what evidence reaches the generator. No
prompt or decoding setting can recover a passage that was never retrieved.

**4.2** Hallucination of an unsupported answer. Controls: an abstention threshold on
retrieval score, a faithfulness check that the cited span contains the claim, and a
measured refusal rate on an unanswerable subset.

**4.3** Larger chunks carry more context but dilute the embedding and waste tokens, so
retrieval precision falls and irrelevant text enters the prompt. Smaller chunks match
queries more precisely but split facts across boundaries. Overlap reduces boundary
loss at the cost of index size and duplicate hits. A fact spanning two chunks may be
retrieved as two partial passages, so the generator sees half the answer.

**4.4** A decorative or unfaithful citation. Citation validity only checks that the id
and span exist; it says nothing about entailment. Preventing it requires a support
check (does the span contain the claim's entities and numbers, does a reader agree) and
a measured unsupported-claim rate.

**4.5** Refuse when the evidence is weak (below threshold) or the request is out of
scope (policy). Metrics in each direction: false-answer rate on unanswerable questions
(danger of answering) and refusal rate on answerable questions, or over-refusal
(cost of cowardice). Report both; tuning one moves the other.

**4.6** Defences: (a) treat retrieved text as data - delimit it, label it untrusted, and
instruct the model not to follow instructions inside it; (b) strip or neutralise
instruction-like content and validate the output against an allowlist; (c)
least-privilege tools so the agent cannot act on the instruction even if persuaded; (d)
human approval for consequential actions. Neither filtering nor prompting is sufficient
alone: filters are bypassed by paraphrase and encoding, and a model can be persuaded by
text that passes the filter. Defence in depth is the claim you can support, not
"the model is immune".

---

## Chapter 5 - Vision, speech, and video

**5.1 - b.** mAP@0.5 is the mean, over classes, of average precision computed with
matches at IoU 0.5. It is not recall at a fixed precision, and it does not say that 78%
of boxes are correct.

**5.2** If the background correlates with the label (all class A photographed on a
bench, class B on a floor), a model can learn the scene and score well without looking
at the object. Test: mask or replace the background, crop tightly to the object, or
evaluate on images with swapped backgrounds. A large accuracy drop indicates the
shortcut.

**5.3** WER = (substitutions + deletions + insertions) / number of reference words,
after an agreed normalisation. It can exceed 1.0 when the hypothesis inserts many words
relative to a short reference, for example a model that emits a long fluent passage for
a three-word reference.

**5.4** Mechanisms: (a) the same vehicle is detected repeatedly as it approaches the
line, so each detection increments the counter; (b) the track is lost and reborn on the
other side, so one vehicle produces two crossings. Fixes: only count when a stable track
id changes side between consecutive matched frames; add hysteresis or require a minimum
displacement; merge reborn tracks by proximity and time, and report the rule.

**5.5** (a) Scale mismatch: objects occupy far more pixels than the model saw, so the
learned receptive field and anchor/grid scales no longer match. (b) Resampling
artifacts and aspect-ratio distortion change texture statistics. Also: per-frame
compute rises quadratically with resolution, and the decision threshold calibrated at
64x64 may be wrong at 1080p.

**5.6** Evidence needed: clips from the second room and camera angle, with the same
label guide; per-class accuracy and macro F1 with intervals; stability across frames;
and a check that background or lighting is not the cue. Meanwhile report the claim as
"0.91 on four-second clips from one camera", state the domain as part of the result, and
list the conditions under which it is untested. Do not generalise from one room.

---

## Chapter 6 - Evaluation, security, and production

**6.1 - b.** Calibration is about the correspondence between predicted probability and
observed frequency, which requires bins with counts. Accuracy, AUC, and loss say nothing
directly about that correspondence.

**6.2** A validation set is labelled, offline, and used to choose the model or
threshold. A monitoring set is production data, mostly unlabelled and often delayed,
used to detect change and trigger investigation. Validation answers "which model";
monitoring answers "is the deployed model still behaving".

**6.3** Pickle can execute arbitrary code during deserialisation, so loading an
untrusted file is remote code execution. Use a weights-only format such as safetensors,
`.npz` arrays, or ONNX, and verify a checksum before loading.

**6.4** Signals: input drift on key features (PSI or KS with a threshold), and a shift
in the prediction distribution or confidence. Also missingness and category novelty.
Action: hold the rollout or keep the canary small, investigate the cause, and prepare a
rollback or retrain with recent data.

**6.5** A canary limits the blast radius and produces real-traffic evidence before full
exposure; it can still fail if the canary traffic is unrepresentative (same region,
same device mix), if the window is too short to see the failure, or if the metric is
aggregated so a subgroup regression is invisible.

**6.6** Control: the send tool is gated behind human approval with a recipient
allowlist, and tool arguments are validated against policy before dispatch; the agent
cannot treat retrieved text as authority to act. Test: index a document containing the
injected instruction, run the task, and assert that no send event occurred, that an
approval was requested (or the action was refused), and that the audit log records the
attempt and the decision.
