# F07 lab - Customer segments for a retention team

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F07 assessment |
| **Time** | About 2 hours |
| **Hardware** | CPU-only |
| **Starter file** | `labs/foundations/f07_customer_segments.md` |
| **Data** | `datasets/foundations/generated/customer_segments.csv`, or generate it with `python scripts/make_foundation_data.py` |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The scenario

A subscription business has a retention team that can run **at most four
campaigns** next quarter. Each campaign needs a target segment and a different
offer. The team has 420 customers described by annual spend, visits per month,
age, and online share. There are no segment labels in the operational data.

A junior analyst clustered the table into three groups, named them "low value",
"core", and "premium", and sent the names to the campaign planner. Before anyone
builds creative around those names, the head of retention asks you three
questions:

1. Is the three-segment solution stable, or did it appear by chance?
2. Would four segments be better for the business, even if the statistics are
   slightly worse?
3. What can we honestly claim about each segment, and what must we not do with
   these labels?

Your job is to answer with evidence and a recommendation, not to rerun the
notebook's plot.

## Why it matters

Segmentation is where descriptive statistics quietly become business decisions.
If a cluster is unstable, a campaign built on it may target a different set of
people next month. If a cluster name implies motive or worth, the campaign can
become manipulative or discriminatory. If four segments are chosen only because
the chart looks tidier, the team may run a campaign it cannot staff.

The technical work is clustering. The professional work is deciding how much
confidence the evidence supports, and saying so in language a retention manager
can act on.

## Constraints

- **Features:** `annual_spend`, `visits_per_month`, `age`, `online_share`, all
  standardized before clustering.
- **Withheld column:** `latent_segment` must not appear in the feature matrix. It
  may be used once, at the end, for evaluation.
- **Sweep:** `k` from 2 through 6, `n_init=10`.
- **Stability:** repeat the chosen `k` with `random_state` values 0, 1, 2, 3, and
  4. Report mean silhouette, its standard deviation, and pairwise ARI between
  runs.
- **Selection rule, fixed in advance:**
  1. highest mean silhouette across the five seeds;
  2. pairwise ARI at least 0.90 for every pair of runs;
  3. every cluster holds at least 10% of rows;
  4. no more than four segments, because the team cannot operate more.
  If criteria conflict, prefer the smaller `k` and explain the trade-off.
- **Profiles:** report feature means in original units, not only z-scores.
- **Supervised check:** stratified 5-fold cross-validation with logistic
  regression on the withheld labels. Report mean accuracy and per-class recall.
- **No individual targeting:** the output is a segment description, not a list of
  customers to contact.

## Required steps

### Step 1 - Provenance and integrity

1. Generate the data if needed:

   ```powershell
   python scripts/make_foundation_data.py
   ```

2. Load `customer_segments.csv` and print the shape, dtypes, missing counts,
   duplicate rows, and the range of each feature.
3. Record the SHA-256 and the generator seed.
4. Create a synthetic `customer_id` before any shuffling, for example
   `C0001` to `C0420`.

**Validation check 1:** assert 420 rows, 5 columns, no duplicate rows, and unique
`customer_id`. Stop and document if a check fails.

### Step 2 - Choose and document the feature set

Write a table with one row per column: name, unit, range, whether it is allowed
as a feature, and why. `latent_segment` is evaluation-only. `customer_id` is an
identifier, not a feature.

**Validation check 2:** assert that `latent_segment` and `customer_id` are not in
the feature list. This must be code, not a sentence in the report.

### Step 3 - Sweep k with five seeds

For each `k` in 2 through 6 and each seed in 0 through 4:

1. Fit k-means with `n_init=10`.
2. Record inertia and silhouette on the standardized matrix.
3. Store the labels for the stability check.

Produce a table of mean silhouette and standard deviation by `k`, plus the mean
inertia. Do not choose `k` from inertia alone.

### Step 4 - Test stability

For the `k` values that pass the silhouette and size criteria, compute pairwise
ARI between the five runs. Report the minimum pairwise ARI.

A solution with a strong silhouette but unstable assignments fails the selection
rule. A stable solution with a weak silhouette is also not enough. Both conditions
must hold.

### Step 5 - Apply the selection rule and decide

Apply the four criteria in order. If `k=3` and `k=4` are close, say so and use the
operational limit to justify the smaller choice. Record the exact numbers behind
the decision in `selection.json`.

A decision table helps:

| Criterion | `k=3` | `k=4` | Passes? |
| --- | --- | --- | --- |
| Mean silhouette | | | |
| Minimum pairwise ARI | | | |
| Smallest cluster share | | | |
| At most four segments | | | |

### Step 6 - Profile and name the segments

Fit the chosen solution once with a recorded seed. For each cluster, report:

- size and share of the base;
- mean and median of each feature in original units;
- one sentence describing the pattern;
- a provisional name of at most four words.

Names must describe behavior in the data, not character judgments. "High-spend,
high-visit" is a description. "Best customers" is a value judgment. "Young and
careless" is both a judgment and an unsupported inference.

### Step 7 - Visualize with PCA

Project the standardized features to two components and plot the clusters.
Report explained variance for both components. State what the plot shows and one
thing it cannot show.

Check that the figure file exists and is non-empty before moving on.

### Step 8 - Evaluate against withheld labels

Compute ARI between your chosen clusters and `latent_segment`. Also build a
cross-table of cluster versus latent segment.

Then run the supervised check: stratified 5-fold cross-validation with logistic
regression, reporting mean accuracy and per-class recall. In a real project these
labels would come from a labeled sample of customers; here they are synthetic and
exist only for evaluation and teaching. Compare what the two evaluations tell you.
They answer different questions and should not be reported as one score.

### Step 9 - Write the memo

Use the report headings below. The memo must:

- recommend three or four segments, with the rule and numbers behind it;
- describe each segment in one sentence and give it a provisional name;
- state one limitation of the clustering and one limitation of the supervised
  check;
- state what the team must not do with the segments;
- include a reproduction section.

## Deliverables

```text
f07-customer-segments/
  README.md                 # how to rerun, in 5-10 lines
  segmentation.ipynb        # executed top to bottom, or segmentation.py plus log
  sweep.csv                 # k, seed, inertia, silhouette
  stability.csv             # pairwise ARI for the candidate k values
  selection.json            # chosen k, rule values, seed
  profiles.csv              # cluster sizes and feature means in original units
  outputs/                  # PCA cluster plot
  segment_memo.md           # the report described below
  reflection.md             # 200-300 words for the assessment
```

`selection.json` should contain the chosen `k`, the seed, mean silhouette,
minimum pairwise ARI, smallest cluster share, and the rule outcome. Do not
include personal paths.

## Report template

```markdown
# F07 customer segmentation memo

## 1. Recommendation
How many segments, which solution, and the one-sentence reason.

## 2. Data and provenance
File, shape, hash, seed, license, and feature units.

## 3. Feature decisions
The allowed and excluded columns, with reasons.

## 4. Choosing k
Silhouette and inertia by k, with the five-seed variation.

## 5. Stability
Pairwise ARI, the minimum, and what it implies.

## 6. Segment profiles
Size, share, original-unit means, one-sentence description, provisional name.

## 7. Visualization
PCA plot, explained variance, and its limits.

## 8. Evaluation
ARI against withheld labels, cross-table, and the supervised cross-validation
result.

## 9. Risks and limits
What the segments cannot support, and what the team must not do.

## 10. Reproduction
Commands, seeds, versions, and artifact locations.
```

## Rubric

The lab is scored on five dimensions. The weights total 100%.

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | Correct scaling, sweep, stability, profiles, and supervised check; assertions pass | Clustering runs but a step is missing or misreported |
| Evaluation and diagnosis | 25 | k chosen by the pre-registered rule; instability and trade-offs discussed; ARI interpreted correctly | k chosen by inertia or preference; stability ignored |
| Reproducibility | 15 | Seeds, hashes, versions, commands, and selection file reproduce every number | Missing seeds or provenance |
| Data and ethics | 15 | No label leakage; names are behavioral; individual targeting and discrimination refused | Names or recommendations overreach the evidence |
| Communication | 15 | Memo is clear to a non-technical manager; numbers and caveats are readable | Jargon or no clear recommendation |

A dimension with no evidence scores zero, regardless of effort.

## Privacy and safety

- The table is synthetic and CC0-1.0. It does not describe real customers. Say so
  in the memo.
- Do not produce a contact list, a ranked list of individuals, or a per-customer
  score. Report segments only.
- Do not use age to justify differential pricing, exclusion, or messaging that
  targets vulnerability. Age is in the table because it is a common feature; that
  does not make every use acceptable.
- Do not name segments with judgments about worth, intelligence, loyalty, or
  character.
- Keep the data local. Do not upload it to a public service or paste it into a
  chat interface.
- Remove absolute personal paths and usernames from logs.

## Self-check before submission

- [ ] The table is 420 x 5 with unique synthetic IDs and no duplicates.
- [ ] `latent_segment` is excluded from the feature matrix by an assertion.
- [ ] The sweep covers `k=2` through `k=6` with five seeds.
- [ ] Pairwise ARI is reported, not just the silhouette.
- [ ] The chosen `k` follows the pre-registered rule, including the operational
      limit.
- [ ] Profiles use original units and names are behavioral, not judgmental.
- [ ] PCA explained variance is reported and the plot file exists.
- [ ] ARI and cross-validated accuracy are reported separately.
- [ ] The memo states what the team must not do with the segments.

Next: score the work with the [assessment](assessment.md), then continue to
[F08 - Regression and classification](../f08-regression-classification/index.md).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
