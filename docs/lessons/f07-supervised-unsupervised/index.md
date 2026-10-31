# F07 - Supervised and unsupervised learning {#f07}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Foundations (M02) |
| **Study time** | 8 hours: 2 h theory, 3 h guided notebook, 2 h lab, 1 h assessment |
| **Hardware** | CPU-only; no GPU required |
| **Prerequisites** | [F06 - Exploratory data analysis and visualization](../f06-eda/index.md) |
| **You will produce** | An executed notebook, a customer segmentation memo, a cluster profile table, and a short reflection |

## Why this module exists

A subscription business has a table of 420 customers: annual spend, visits per
month, age, and share of orders placed online. The marketing team asks two
questions in the same meeting:

1. "What kinds of customers do we have?" There are no labels for this. Nobody has
   defined the kinds yet.
2. "Which customers will accept the next offer?" For a small sample, the team has
   outcome labels: accepted or not.

These look like the same problem because they use the same table. They are not.
The first question is **unsupervised**: find structure without a target. The
second is **supervised**: learn a mapping from features to a known outcome. They
need different methods, different evidence, and different claims.

The common failure is to blur them. Someone clusters customers, notices that one
cluster spends more, and announces that the cluster *causes* higher revenue.
Someone else trains a classifier on labels, gets 100% accuracy on well-separated
synthetic data, and promises the same in production. This module teaches you to
keep description and prediction separate, and to evaluate each with the right
tool.

## Learning objectives

By the end of this module, you can:

1. Decide whether a question needs supervised or unsupervised learning, based on
   whether a target exists.
2. Standardize features and explain why distance-based methods fail without
   scaling.
3. Run k-means for a range of `k` and choose a solution using inertia, silhouette,
   and stability rather than inertia alone.
4. Profile clusters with feature means and describe them without causal or
   stigmatizing claims.
5. Evaluate clustering against withheld labels with the adjusted Rand index and
   explain how it differs from classification accuracy.
6. Use PCA to project high-dimensional data to two dimensions and interpret the
   explained variance.
7. Train a supervised baseline on labeled data and compare its claim with the
   clustering result.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| Completed [F06](../f06-eda/index.md) | You need to inspect distributions before clustering them |
| pandas, NumPy, scikit-learn, matplotlib | The notebook imports all four |
| The customer table, or the generator | The notebook builds the table itself |
| About 8 GB of RAM | Ample; the table is 420 rows |
| A scratch folder for figures | The notebook writes `outputs/f07_clusters.png` |

The notebook generates the customer table with a fixed seed. To work from CSV,
run `python scripts/make_foundation_data.py` and read
`datasets/foundations/generated/customer_segments.csv`. The
[dataset card](../../technical/foundation-assets.md#foundation-datasets) explains that
`latent_segment` is withheld for evaluation; the generator is
[`scripts/make_foundation_data.py`](../../technical/foundation-assets.md#data-generator).

## The concepts you need

### 1. Two learning problems

| | Supervised | Unsupervised |
| --- | --- | --- |
| Data | Features plus a target | Features only |
| Question | What is the target for this row? | What structure exists in these rows? |
| Output | A prediction or probability | Groups, components, or distances |
| Typical methods | Linear regression, logistic regression, trees | k-means, hierarchical clustering, PCA |
| Evidence | Accuracy, precision, recall, error | Silhouette, stability, domain review |
| Main failure | Leakage and overfitting | Reading structure into noise |

A **target** is the column you want to predict. If it exists for enough rows, the
problem is supervised. If it does not, or if you are not trying to predict it, the
problem is unsupervised.

The customer table has a `latent_segment` column, but it is generated for
evaluation and is normally hidden. Using it as a clustering input would be
**target leakage**: the algorithm would be handed the answer it is supposed to
discover.

### 2. Features, scale, and distance

K-means groups rows by distance, usually Euclidean distance in feature space. If
the features have different units, the largest-numbered feature dominates.

In the customer table, annual spend ranges from about 26 to 1,320, visits per
month from 0.2 to 22.8, age from 18 to 61, and online share from 0 to 0.99. A
difference of 500 in spend is ordinary; a difference of 500 in online share is
impossible. Without scaling, the distance is effectively "spend
distance plus a rounding error".

**Standardization** replaces each column with its z-score:

```python
z = (x - mean) / standard_deviation
```

After standardization, each feature has mean 0 and standard deviation 1, so one
standard deviation means the same thing in every column. The notebook asserts
that the column means are zero to within 1e-9.

For supervised work, fit the scaler on training rows only, as in F05. For
unsupervised work there is no target to leak, but you should still record the
mean and standard deviation so the transformation can be reproduced and applied
to new rows.

### 3. K-means in plain terms

**K-means** partitions rows into `k` groups by repeating two steps:

1. Assign each row to its nearest centroid.
2. Move each centroid to the mean of its assigned rows.

It stops when assignments stop changing or a maximum iteration count is reached.
`n_init=10` runs the procedure from ten different starting points and keeps the
best result, which reduces the chance of a poor local minimum.

**Inertia** is the sum of squared distances from each row to its centroid. It
always falls as `k` increases, because more centroids can only fit the data more
closely. That makes inertia useless as a standalone choice of `k`.

Worked example with one feature and the points 1, 2, 3, 4, 10, 11, 12, 13:

| `k` | Best partition | Inertia |
| --- | --- | --- |
| 1 | all eight points | 172.0 |
| 2 | 1-4 and 10-13 | 10.0 |
| 3 | 1-4, 10-11, 12-13 | 6.0 |
| 4 | four pairs | 2.0 |

Inertia keeps falling, yet `k=4` is not obviously better than `k=2`. The two
groups at 1-4 and 10-13 are far apart; splitting pairs inside each group adds
complexity without discovering a new structure. You need a measure that rewards
separation as well as compactness.

### 4. Choosing k with silhouette, stability, and purpose

The **silhouette score** for a row compares its average distance to its own
cluster (`a`) with its average distance to the nearest other cluster (`b`):
`(b - a) / max(a, b)`. It ranges from -1 to 1. Values near 1 mean the row is much
closer to its own cluster; values near 0 mean it sits between clusters; negative
values mean it may be in the wrong cluster.

The overall score is the mean over rows. A common rule of thumb:

| Silhouette | Rough reading |
| --- | --- |
| Above 0.5 | Reasonable, well-separated structure |
| 0.25 to 0.5 | Weak structure; inspect before acting |
| Below 0.25 | No substantial structure at this `k` |

The verified k-means sweep produced:

| `k` | Silhouette |
| --- | --- |
| 2 | 0.619 |
| 3 | 0.707 |
| 4 | 0.552 |
| 5 | 0.363 |
| 6 | 0.246 |

The maximum is at `k=3`, so the notebook chooses three clusters. Notice that
`k=2` also has a healthy score. A high silhouette does not prove that three is
the "true" number of segments; it says that three is the best-separated solution
among those tested for this feature set.

Two more checks matter:

- **Stability.** Rerun with different seeds or bootstrap samples and compare the
  assignments. A solution that changes every run is not a finding.
- **Purpose.** A segmentation that supports three different actions is more
  useful than a four-cluster solution nobody can act on. This is a judgment, and
  it must be stated as one.

### 5. Clusters are descriptions, not causes

After fitting, profile each cluster with the mean of every input feature. In the
verified run the cluster sizes are 143, 110, and 167.

A profile might read: "cluster 0 has lower spend, fewer visits, younger customers,
and a higher online share". That is a description of the rows assigned to the
cluster. It is not evidence that online behavior causes low spend, and it is not a
persona with motives.

Three rules keep cluster descriptions honest:

1. Describe the centroid in the units of the input features.
2. Name a cluster only after checking the profile, and make the name provisional.
3. Do not attach a decision to a cluster without a separate, supervised test of
   that decision.

### 6. Evaluating clustering with withheld labels

The **adjusted Rand index (ARI)** compares two label assignments. It is 1.0 when
the partitions are identical up to relabeling, near 0 when agreement is what
chance would produce, and can be negative for worse-than-chance agreement.

In the notebook, the clustering is fitted without `latent_segment`. Afterward,
ARI between the discovered clusters and the withheld segment is **1.0**. That is
expected: the generator created three well-separated groups. Real data is
messier, and a high ARI on synthetic data is a ceiling, not a promise.

ARI is not accuracy. Accuracy compares a predicted label with a known label and
depends on which cluster is called "0" or "2". ARI is invariant to relabeling and
compares the *partition*, which is the right question when clusters have no
canonical names.

### 7. Two supporting tools: PCA and a supervised baseline

**PCA is a summary, not proof.** Principal component analysis (PCA) finds new
axes that capture the most variance in the standardized features. The first
component is the direction of greatest variance; the second is the next direction,
perpendicular to the first.

The notebook projects the four features onto two components for plotting. The
explained variance is **93.8%** for the first component and **3.0%** for the
second, about 96.8% combined. The 2D plot therefore preserves most of the
variation, which makes it a fair summary here.

Two cautions:

- A 2D plot can make clusters look cleaner than they are. The third and fourth
  dimensions still exist.
- PCA is not a clustering method. It rotates the data; it does not assign groups.

**A supervised baseline answers a different question.** If segment labels exist
for a sample, a classifier can learn to predict them for new customers. The
notebook trains logistic regression on a stratified 70/30 split and reaches
accuracy **1.0** on the held-out rows. Again, the synthetic groups are far apart;
real classification is rarely perfect.

| Claim | Method | Evidence | What it does not prove |
| --- | --- | --- | --- |
| The base contains three groups | Clustering | Silhouette, profiles, ARI | That the groups are real customer types |
| This customer belongs to group 2 | Classification | Held-out accuracy, recall | That the group causes behavior |
| Two components explain most variation | PCA | Explained variance | That the remaining variance is irrelevant |

## Guided walkthrough

The [guided notebook](notebook.md) runs six sections on the customer table:

1. **Build the table.** Generates 420 customers, standardizes four features, and
   asserts the standardized means are zero.
2. **Choose k.** Fits k-means for `k=2` through `k=6`, records inertia and
   silhouette, and asserts that the best silhouette is at `k=3`.
3. **Fit and profile.** Fits three clusters and prints feature means and cluster
   sizes: 143, 110, and 167.
4. **Evaluate with withheld labels.** Computes ARI against `latent_segment`; the
   result is 1.0.
5. **Visualize with PCA.** Projects to two components, prints 93.8% and 3.0%
   explained variance, and saves `outputs/f07_clusters.png`.
6. **Supervised comparison.** Trains logistic regression on a labeled subset and
   reports accuracy 1.0.

The notebook never uses `latent_segment` as an input. If you add it to the
feature matrix, the ARI becomes meaningless and the exercise collapses.

## Practical exercise

This exercise is smaller than the lab and stays inside the notebook's data. Work
in a scratch notebook.

1. Cluster using only `annual_spend` and `visits_per_month`, standardized. Run
   `k=2, 3, 4` and record silhouette for each.
2. Compare the best two-feature silhouette with the four-feature values in the
   notebook.
3. Rerun the four-feature `k=3` model with `random_state` 0, 1, and 2. Compute ARI
   between the first run and each of the others.
4. Project the two-feature solution with PCA and plot it.

Expected observations:

- If the two-feature silhouette is close to 0.707, spend and visits carry most of
  the separation. If it is much lower, age and online share are doing real work.
  Record which, do not assume.
- The ARI between the three four-feature runs should be close to 1.0 because the
  groups are well separated and `n_init=10` stabilizes the solution. A low value
  would mean the clustering is unstable and the `k` choice needs review.
- The two-feature PCA plot should show three bands if spend and visits separate
  the groups. A single blob means the discarded features were important.

## Common mistakes and how to diagnose them

| Mistake | Symptom | Diagnosis and fix |
| --- | --- | --- |
| Clustering unscaled features | One feature dominates every distance | Compare feature ranges; standardize before fitting |
| Choosing `k` by inertia | Best `k` is always the largest tested | Plot silhouette; inertia always decreases |
| Using `latent_segment` as an input | ARI is high but the task is circular | Drop the column before `fit`; keep it only for evaluation |
| Evaluating clustering with accuracy | Label permutation changes the score | Use ARI or another partition measure |
| Calling clusters "types of people" | Confident personas from one run | Report profiles as descriptions; test stability |
| Reading a PCA plot as proof | "The clusters are real because they separate" | Check silhouette and stability in the full feature space |
| Ignoring cluster sizes | A 4-row cluster drives the story | Print sizes; set a minimum for interpretation |
| No `random_state` | Assignments change on every run | Fix the seed and record it |

## Checkpoint

You are ready for the lab when you can:

- [ ] State whether a question needs labels, and why.
- [ ] Explain what standardization does to a distance and why it matters here.
- [ ] Explain why inertia cannot choose `k`.
- [ ] Read the silhouette table and defend `k=3` without claiming it is the truth.
- [ ] Describe a cluster using feature means in original units.
- [ ] Explain why ARI 1.0 is expected on this synthetic table and not a promise
      for real data.
- [ ] Interpret 93.8% plus 3.0% explained variance without overclaiming.

## Next step

1. Run the [guided notebook](notebook.md) and open the saved cluster plot.
2. Complete the [lab brief](lab.md): segment the customer base under new
   constraints, test stability, and recommend how many segments the retention
   team should run.
3. Score your work with the [assessment](assessment.md).
4. Continue to [F08 - Regression and classification](../f08-regression-classification/index.md).

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
