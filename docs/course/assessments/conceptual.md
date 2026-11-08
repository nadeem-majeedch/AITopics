# Conceptual questions

```markdown
**Assessments:** [Overview](index.md) · **Conceptual** · [Solutions](solutions/conceptual.md)
```

Twenty questions that require an explanation, not a definition. Aim for three to six
sentences each. A good answer names the mechanism, the consequence, and one condition
under which it fails.

Mark with the four-level scale in the [overview](index.md). The standard for
"Excellent" is in the [solutions](solutions/conceptual.md), including the points a
strong answer must contain.

---

## Data and evaluation

**1.** Why is a held-out test set meaningless if you use it to decide between twenty
models, even if you never train on it?

**2.** Two teams report 0.85 accuracy on the same task with different class
distributions. Explain why the numbers may not be comparable and what you would ask
for.

**3.** A feature is recorded after the outcome is known. Explain how it enters the
model and why cross-validation will not save you.

**4.** Explain the difference between *uncertainty* and *error*. Why does a
well-calibrated model still make mistakes, and why is that acceptable?

**5. (advanced)** Your dataset has 4% of one class. Describe how you would choose
between resampling, class weights, and threshold tuning, and what evidence would
make you change your choice.

## Modelling

**6.** Explain why adding features can reduce test accuracy even when every feature
is genuinely predictive.

**7.** A gradient-boosted model and a logistic regression have identical AUC, but the
boosted model's probabilities are pushed toward 0 and 1. Which would you deploy for
a human-reviewed queue, and why?

**8.** Describe what a learning curve (training size versus validation score) tells
you that a single validation number does not.

**9.** Why can a model with lower average error be worse for a specific subgroup than
a model with higher average error? Give a concrete decision consequence.

**10. (advanced)** You must justify choosing a 135M fine-tuned model over a 7B
prompted model. List four comparisons you would run and what result would change
your choice.

## Generative systems

**11.** Explain why retrieval quality and answer quality must be measured
separately in a RAG system.

**12.** A model answers correctly but cites the wrong passage. Explain two distinct
causes and one test for each.

**13.** Why does a longer context window not solve grounding? Refer to attention,
cost, and evaluation in your answer.

**14. (advanced)** Describe how you would decide whether to fine-tune a model or
improve retrieval for a document-assistant product. Name the experiment that would
settle it and the metric you would use.

## Deployment and responsibility

**15.** Explain why offline evaluation cannot tell you how a system will behave
after deployment, using one concrete example.

**16.** A stakeholder asks for "no false negatives". Explain why this request is
incomplete and what you need before you can answer it.

**17.** Describe the difference between a model card and a system card, and why a
system may need both.

**18. (advanced)** An agent has read access to all company documents and a send
tool. Explain the confused-deputy problem in this design and one control that
addresses it.

**19.** Why is "we will log everything" not a privacy control? Name two things a
logging policy must specify.

**20. (advanced)** Your model improves a metric by 3 points but requires 40x the
compute. Describe the analysis you would present, including the conditions under
which the trade is justified and the conditions under which it is not.
