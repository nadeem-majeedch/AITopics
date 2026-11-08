# Conceptual questions - model answers

```markdown
**Assessments:** [Overview](../index.md) · [Solutions](index.md) · [Conceptual](../conceptual.md)
```

Each answer states the mechanism and the consequence. Score 4 if your answer contains
the mechanism and at least one condition under which it fails, 3 if it contains the
mechanism, 2 if it has the vocabulary but not the reasoning.

Several questions have more than one defensible framing; the notes say what an
alternative answer must include to be equally strong.

---

## Data and evaluation

**1.** Repeated evaluation on the same test set turns it into a validation set: each
decision between twenty models uses a little information from the test set, so the
reported winner is selected partly for noise. The score becomes optimistic by an amount
that grows with the number of comparisons and shrinks with test size. Use validation for
selection, then one final test run, or keep a second untouched set. A strong answer adds
that the bias is not visible in the number itself, which is why the protocol matters
more than the arithmetic.

**2.** Accuracy depends on prevalence: the same model scores differently on different
class mixes, and a 0.85 on a 50/50 set is not the same claim as 0.85 on a 5% set. Ask
for the class distribution, the confusion matrix, and the metric definitions; then
whether the test sets were drawn from the same population as deployment. Precision,
recall, and per-class results make the comparison meaningful. Alternative framing:
reporting balanced accuracy or macro F1 resolves part of the issue but still needs the
counts.

**3.** A post-outcome feature is unavailable at prediction time but present in training
data, so the model learns a rule that cannot be applied in production: the feature
itself encodes the label, and the learned relationship is with the recording process,
not the outcome. Cross-validation does not help because the leakage is inside every
fold. The check is temporal and procedural: for each feature, state when it is recorded
and whether it exists for a row whose outcome is not yet known.

**4.** Error is being wrong; uncertainty is how much the model's output should be
trusted. A calibrated model that says 0.7 is right about 70% of the time still errs on
30% of those cases, because the outcome is stochastic given the features. That is
acceptable when the decision accounts for it: the human reviews the uncertain cases and
the cost of the residual errors is bounded. A model that is accurate but
overconfident is worse for review, because it hides which cases need attention.

**5.** Resampling changes the effective class balance and can duplicate rows, risking
leakage if done before the split; class weights keep the data intact and change the
loss; threshold tuning changes neither and simply moves the operating point. Choose
threshold tuning first when the metric is operational and the ranking is already good;
class weights when the model is unstable on the minority class; resampling when the
minority class is too sparse to learn from, and only inside the training fold. Evidence
that would change the choice: per-class recall and calibration on held-out data, and
whether the intervention improved the operating point at the same false-positive
budget.

## Modelling

**6.** Each added feature adds variance to the estimate: with finite data, the model can
fit spurious relationships, and the improvement in training fit does not transfer.
Correlated features split importance unstably, and multiple testing across many
candidates inflates the chance of a lucky fit. Test accuracy falls when the variance
term grows faster than the bias term falls. A strong answer notes that "predictive" is a
population claim, and the sample is what the model actually sees.

**7.** For a human-reviewed queue, the calibrated model: the reviewer needs to know
whether 0.8 means eight-in-ten, so they can prioritise and set a review threshold.
Identical AUC means the ranking is equivalent, so the choice comes down to the meaning
of the score. A boosted model can be calibrated after the fact, so the real answer is
"the one that is calibrated and stable", with the caveat that calibration must be
verified on held-out data rather than assumed.

**8.** A learning curve shows whether more data would help: if training and validation
scores converge at a low value, the model is underfitting and more data will not help;
if a persistent gap remains, more data or regularisation may. A single validation number
cannot distinguish "limited by data" from "limited by model capacity" or "limited by
label noise". It also exposes how uncertain the estimate is at small sample sizes.

**9.** Averages weight by group size, so a large group with small errors can mask a small
group with large errors. If the small group is the one the decision affects - a clinic, a
device type, a region - the average is the wrong summary and the decision harms that
group while the dashboard looks fine. The consequence is that the model should be
selected and monitored on per-slice metrics with minimum sample sizes, not on a single
aggregate.

**10.** Compare: quality on a held-out task with a fixed rubric; cost per request,
including GPU minutes and latency; the ability to fit the task in context; privacy and
data-handling constraints; and maintenance burden when the data changes. Also compare
failure modes: a fine-tuned small model can be more consistent in style but worse on
unseen instructions, while a prompted large model may follow instructions better but
drift in format. The result that changes the choice is a statistically distinguishable
quality gap at an acceptable cost, or a hard constraint (privacy, offline, latency) that
eliminates one option. Alternative answer: insist on a cost-per-successful-task metric,
which combines quality and price and is often the decision-relevant number.

## Generative systems

**11.** Retrieval decides whether the evidence is available; generation decides whether
the answer uses it faithfully. A system can retrieve the right passage and still
hallucinate, or retrieve the wrong passage and produce a correct-sounding answer from
parametric knowledge. Averaging them hides which component to fix, so measure
recall@k/MRR for retrieval and supported-claim rate for generation, then combine them
only for the end-to-end view.

**12.** (a) The generator attached a real but irrelevant passage: the citation resolves
because it was retrieved, but the claim came from elsewhere; test by checking whether
the cited span contains the claim's entities and numbers. (b) The retriever found the
right document but the wrong span, so the citation points at a neighbouring paragraph;
test by span-level support labels rather than document-level. Both produce the same
symptom, which is why "citation resolves" is a weak metric.

**13.** A longer window does not make the model use the right part of it: attention is
spread over more text, and the relevant passage competes with distractors. Cost grows
with tokens, and evaluation becomes harder because more context means more ways to be
accidentally right. Grounding requires retrieval precision, explicit citation, and a
support check, not capacity. The failure mode of long context is a confident answer
built from an irrelevant paragraph that happened to be included.

**14.** Fine-tuning teaches style, format, and task-specific behaviour; retrieval
supplies facts. If failures are factual or coverage-related, improve retrieval and
measure recall and supported-claim rate. If failures are format, tone, or instruction
following, fine-tune and measure with a rubric. The settling experiment: hold the
retriever fixed and compare prompted versus fine-tuned on the same held-out questions,
then hold the model fixed and compare retrieval configurations. Choose the intervention
with the larger measured effect per unit cost, and report both.

## Deployment and responsibility

**15.** Offline evaluation uses a fixed distribution and labelled outcomes; production has
a changing population, delayed labels, and feedback loops. Example: a model trained on
desktop sessions is deployed to mobile users whose behaviour differs, so accuracy on the
old test set says nothing about the new traffic. Only production monitoring - input
drift, prediction distribution, delayed outcome metrics - can detect it. A strong answer
adds that the deployment decision needs a rollback path, because detection without
recovery is incomplete.

**16.** "No false negatives" is incomplete because it does not say at what cost in false
positives, on which population, for which class, or over what time window; a model can
achieve zero false negatives by predicting positive for everything. You need the
operating cost of a false positive, the acceptable review volume, the recall target with
a confidence interval, and the subgroup requirements. Then the request becomes a
trade-off you can test.

**17.** A model card describes the model: training data, metrics, intended use, and
limitations of the predictor. A system card describes the deployed system: retrieval,
prompts, tools, access controls, human oversight, logging, and failure handling. A
system with a model inside needs both because most real failures are interaction
failures - retrieval, interface, permissions - that the model card cannot describe.

**18.** The agent acts with the user's authority but can be steered by content it reads:
a document tells it to send data, and the send tool executes with the user's
permissions, so the deputy (the agent) is confused about whose instruction it follows.
The control is to separate data from instructions: treat retrieved text as untrusted,
require human approval for sends, restrict recipients to an allowlist, and validate the
action against policy at dispatch. A strong answer notes that prompt-level defences alone
are bypassable, so the enforceable control is at the tool boundary.

**19.** Logging everything creates a new sensitive dataset with its own breach, retention,
and access risks; it is surveillance unless bounded. A logging policy must specify what
is recorded (and what is redacted), how long it is kept, who can read it, and how a
subject can have it deleted. "We log everything" answers none of those.

**20.** Present the trade-off, not a single delta: quality gain with an interval, cost
increase in money, latency, and energy, and the conditions under which the gain matters
(is 3 points above the decision threshold? does it change the human review load?).
Justified when the metric is the decision metric, the gain survives uncertainty, and the
cost is within budget; not justified when the gain is inside the interval, when latency
breaks the use case, or when the same gain is available from a cheaper intervention such
as threshold tuning or better retrieval. Also state who pays the cost and who receives
the benefit, because they are often different.
