# End-of-course revision questions

```markdown
**Assessments:** [Overview](index.md) · **Revision** · [Solutions](solutions/revision.md)
```

Thirty questions for the last week. Answer closed-book in one or two sentences, then
check [solutions/revision.md](solutions/revision.md). If an answer needs more than
three sentences, you have found a topic to reread.

**Scoring:** one point per question if the answer contains the mechanism; half a point
if it is correct but incomplete. Total out of 30.

---

## Part 1 - Data and evaluation (1-8)

1. What is the difference between a validation set and a test set?
2. Name two ways leakage enters a tabular pipeline without an obvious ID column.
3. Why is accuracy a poor headline metric for a 3%-positive dataset?
4. What does a bootstrap confidence interval estimate?
5. What does calibration mean, in one sentence?
6. Why must augmentation be applied to training data only?
7. What is the difference between a slice and a subgroup, if any?
8. When is a small test set still useful?

## Part 2 - Modelling and training (9-15)

9. What does regularisation trade away, and for what?
10. Why can a deeper tree have lower training error and higher test error?
11. What is the role of the learning rate in gradient descent?
12. Why does batch normalisation change training dynamics?
13. What is overfitting in a fine-tuned language model, concretely?
14. Why is a frozen backbone often better than full fine-tuning on a small dataset?
15. What does a learning curve tell you that a single score does not?

## Part 3 - Generative and retrieval systems (16-20)

16. What does retrieval add to a language model that prompting alone does not?
17. Why is chunk overlap used, and what does it cost?
18. What is the difference between a citation resolving and a citation supporting a
    claim?
19. Name two metrics for RAG that are not answer accuracy.
20. Why can prompt injection arrive through a retrieved document?

## Part 4 - Vision, speech, video (21-25)

21. What does IoU measure, and what does mAP average over?
22. Why does class imbalance in object instances affect per-class AP?
23. What is word error rate, and what does it not measure?
24. Why does counting by detection alone over-count vehicles?
25. What is the difference between a frame-based and a temporal video model?

## Part 5 - Production and responsibility (26-30)

26. What is the difference between monitoring inputs and monitoring outcomes?
27. Why is a canary release not a guarantee of safety?
28. What is the security risk of loading an untrusted pickle file?
29. Name three controls that bound what an agent can do.
30. What must a model card say that a README usually does not?
