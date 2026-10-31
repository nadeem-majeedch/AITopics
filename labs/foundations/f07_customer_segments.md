# F07 customer segments - submission template

Use this file as the starting point for the lab required by the
[F07 lab brief](../../docs/lessons/f07-supervised-unsupervised/lab.md). Replace
every bracketed prompt with your own evidence. Delete prompts you did not answer.

Save your completed copy outside the course repository, for example:

```text
portfolio/f07-customer-segments/segment_memo.md
```

## Scenario summary

[Three sentences: the retention team, the four-campaign limit, and the number of
segments you recommend.]

## Constraints I worked under

| Constraint | Value |
| --- | --- |
| Features | `annual_spend`, `visits_per_month`, `age`, `online_share` |
| Forbidden input | `latent_segment` (evaluation only) |
| Identifier | Synthetic `customer_id`; never a feature |
| Sweep | `k=2` to `k=6`, `n_init=10` |
| Stability seeds | 0, 1, 2, 3, 4 |
| Selection rule | Highest mean silhouette, minimum pairwise ARI 0.90, each cluster at least 10%, at most four segments |
| Supervised check | Stratified 5-fold logistic regression |

## Commands and seeds

```powershell
# [exact commands, including data generation]
```

| Item | Value |
| --- | --- |
| Data file and SHA-256 | [value] |
| Shape | [rows x columns] |
| Python / pandas / scikit-learn | [versions] |
| Chosen `k` and seed | [values] |
| Number of k-means fits | [value] |
| Test or CV folds | [value] |

## Required artifacts

| Artifact | Path | Present |
| --- | --- | --- |
| Executed notebook or script log | [path] | [yes/no] |
| Sweep table | `sweep.csv` | [yes/no] |
| Stability table | `stability.csv` | [yes/no] |
| Selection record | `selection.json` | [yes/no] |
| Profiles | `profiles.csv` | [yes/no] |
| PCA figure | `outputs/*.png` | [yes/no] |
| Memo | `segment_memo.md` | [yes/no] |
| Reflection | `reflection.md` | [yes/no] |

## Sweep and selection to fill in

| `k` | Mean silhouette | SD | Mean inertia | Min pairwise ARI | Smallest share | Passes rule |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |

**Chosen `k`:** [value]  
**Why:** [rule values and operational constraint in two sentences]

## Segment profiles to fill in

| Cluster | Size | Share | Spend | Visits | Age | Online share | Description | Name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | | | | | | | | |
| 1 | | | | | | | | |
| 2 | | | | | | | | |

Profiles must be in original units. Names are at most four words and describe
behavior, not worth.

## Report headings

```markdown
# F07 customer segmentation memo

## 1. Recommendation
## 2. Data and provenance
## 3. Feature decisions
## 4. Choosing k
## 5. Stability
## 6. Segment profiles
## 7. Visualization
## 8. Evaluation
## 9. Risks and limits
## 10. Reproduction
```

## Validation checks

- [ ] 420 rows, 5 columns, no duplicates, unique synthetic IDs.
- [ ] `latent_segment` and `customer_id` excluded from features by an assertion.
- [ ] Every cluster has at least 10% of rows.
- [ ] The chosen `k` satisfies every clause of the selection rule, or the
      trade-off is documented.
- [ ] The PCA figure exists and the explained variance is reported.

## Rubric reminder

| Dimension | Weight |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |

A dimension with no evidence scores zero. Full descriptors are in the
[lab brief](../../docs/lessons/f07-supervised-unsupervised/lab.md#rubric).

## Privacy and ethics check

- [ ] The memo says the data is synthetic and not about real customers.
- [ ] No contact list, individual score, or ranked customers.
- [ ] Age is not used to justify exclusion or vulnerability targeting.
- [ ] Segment names do not judge worth, loyalty, or character.
- [ ] No differential pricing recommendation without a controlled test.
- [ ] No absolute personal paths or usernames in logs.
