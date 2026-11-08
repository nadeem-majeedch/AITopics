# Scenario-based questions - model answers

```markdown
**Assessments:** [Overview](../index.md) · [Solutions](index.md) · [Scenarios](../scenarios.md)
```

There is rarely one right decision. What matters is that the decision is stated, the
evidence is named, and the conditions that would change it are explicit. Each entry
gives one defensible position, the evidence it rests on, and an alternative that is
equally strong if argued well.

---

## S1 - The 98% classifier

**Defensible decision:** run a pilot only after a paid or free evaluation on your own
labelled sample, and do not sign based on 98%.

**Why:** with 12 categories and a 46% majority class, 98% accuracy is compatible with
excellent performance on the large classes and near-zero recall on the small ones. The
decision that matters is routing, and a misroute has a cost per ticket. You need the
confusion matrix, per-class precision and recall at the proposed threshold, and the
abstention behaviour.

**Smallest experiment:** sample 400 of your own tickets, stratify by category, label
them, and evaluate the vendor's model through its API on that sample. Report macro F1,
per-class recall, and the review rate at their threshold. If the vendor refuses any
access, that is itself a finding.

**Alternative position:** decline outright if the vendor will not expose per-class
metrics - a black-box pilot cannot answer the question you need answered. Both
positions are acceptable if the reasoning is explicit.

---

## S2 - The leak you find after the report

**Defensible decision:** ship the corrected version tomorrow, with the leak, the inflated
number, and the corrected number visible, plus a short note on how it was caught.

**Why:** the 0.94 is not a result; it is an artefact of a feature that is populated only
for churned customers. Keeping it in the headline would mislead whoever acts on the
model. Reporting both numbers is stronger than quietly replacing one, because it shows
the audit worked and gives the reader a calibration for future claims.

**What to do with 0.94:** keep it as a labelled demonstration of the failure mode, not as
a performance claim, and recompute the model without the column. Report the drop and
whether the remaining model still supports the decision.

**Process change:** an automated availability check per feature (when is it recorded?),
a leakage audit in the template, and a rule that any feature added after the split must
be justified in writing. **Alternative:** delay the deadline by a day to re-run
properly, if the audience can absorb it; do not delay silently.

---

## S3 - The fine-tune that is not better

**Defensible decision:** do not ship; run one more comparison with a larger, blinded
rubric sample, and decide on cost-adjusted quality.

**Why:** 3.4 versus 3.2 on 20 items is well within rater noise; a 0.2 difference on a
five-point scale with 20 samples is not evidence. Latency is 1.8x higher and the adapter
adds maintenance. The comparison also needs identical prompts and decoding, a rubric
fixed before scoring, and ideally a second rater or a re-score a day later.

**What would justify shipping:** a difference that survives a larger sample (for example
60-80 items) and blind scoring, at a cost the product can absorb, with no regression on
policy compliance. **Alternative:** ship it behind a flag for a low-risk slice and
measure edit rate on real drafts - a production signal that is cheaper than more offline
annotation, provided the flag has a rollback.

---

## S4 - The citation that looks right

**Defensible decision:** not ready for internal use; the citation is decorative and the
corpus contains a contradiction that the system resolves silently.

**Why:** recall@5 of 0.92 says the evidence was available. It does not say the cited
passage supports the sentence. Here the cited document gives 5-10 working days, the claim
says 14, and a third document gives 14 for annual plans. That is a faithfulness failure
plus a conflict the system should surface rather than average.

**Label:** "unsupported citation with a conflicting source" - a distinct category from
"wrong document retrieved".

**First change:** a support check that requires the claim's numbers and entities to
appear in the cited span, plus contradiction detection that returns both passages with
their scope. Re-measure the unsupported-claim rate before reopening the rollout.

**Alternative:** restrict the pilot to questions whose answers are single-document and
numeric-free, and state that restriction; defensible only if the restriction is enforced,
not just documented.

---

## S5 - The camera in the second room

**Defensible decision:** deploy nothing to the new sites yet; offer a two-week
measurement pilot with a human-verified count sample.

**Why:** 1.4 vehicles MAE on the tuning clip is an in-sample result. New angles change
perspective, occlusion, and vehicle scale; night changes contrast and headlight glare.
The failure you are most worried about is a systematic under-count at night, which looks
like "less traffic" and is easy to accept.

**Evidence to collect:** one hour of footage per site at peak and off-peak, hand-counted
ground truth for four 5-minute windows per condition, and per-site MAE with intervals.
Report per-site and per-condition; do not pool sites into one number.

**What to promise:** a measured error range for the conditions tested, a human review
step, and a rollback to manual counts. Do not promise enforcement-grade accuracy.

---

## S6 - The agent that wants to send

**Defensible decision:** the agent summarises, then requests approval to send; it does
not forward contacts, and it reports the injected instruction.

**Why:** the instruction arrives as data inside a document. The agent's authority comes
from the employee, not from the document, so the document cannot authorise a send. The
summary itself is fine if it contains only the requested pipeline information.

**Step by step:** (1) read documents and CSV under the employee's role; (2) detect the
instruction-like line and treat it as content to report, not to follow; (3) compose the
summary; (4) request approval for the send, showing recipient and a content preview;
(5) on denial, return the summary without sending; (6) write the attempt and decision to
the audit log.

**Controls:** least-privilege recipient allowlist, approval before dispatch, output
validation that blocks external addresses, and an audit trail. **Test:** index a document
with the injected line, run the task, assert no send occurred and the audit records the
blocked attempt.

---

## S7 - The licence that is unclear

**Defensible decision:** do not use the dataset; find a licensed substitute or generate
one.

**Why:** "available for research" typically excludes redistribution of the images and
often excludes public model weights trained on them. A public GitHub repository is
redistribution. "Everyone uses it" is not a licence, and a portfolio piece built on
unclear terms cannot be shared safely.

**What to ask:** whether derivative works (trained weights) may be published, whether
images may be redistributed, whether commercial use is excluded, and what attribution is
required. Get it in writing, with a URL and a date.

**Fallback:** use the course's generated dataset, or a clearly licensed public set, and
state the substitution in the report. **Alternative:** keep the unlicensed data for a
private experiment and publish only the method and the licensed-data results - acceptable
only if no derived weights or images are published.

---

## S8 - The metric that moved

**Defensible decision:** hold the rollout, keep traffic on the previous model, and
investigate the mobile slice before promoting.

**Why:** unchanged aggregate AUC can hide a regression in a growing segment: mobile
sessions doubled, so the aggregate is now dominated by a population the model was not
trained on. The support team's report is a qualitative signal that the aggregate is
masking something.

**Slices to compute first:** mobile versus desktop, new product line versus existing,
and session length; per-slice AUC, calibration, and suggestion acceptance if available.
Then compare the prediction distribution for mobile before and after retraining.

**Canary:** route 5-10% of mobile traffic to the new model, measure acceptance and
override rate for a week, with a pre-registered rollback threshold (for example a 3-point
drop in acceptance or a calibration error above 0.1). **Alternative:** promote only on
desktop and keep the old model for mobile while a mobile-specific model is trained; that
is defensible if the split is implementable and documented.
