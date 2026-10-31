# F06 house EDA - submission template

Use this file as the starting point for the lab required by the
[F06 lab brief](../../docs/lessons/f06-eda/lab.md). Replace every bracketed prompt
with your own evidence. Delete prompts you did not answer.

Save your completed copy outside the course repository, for example:

```text
portfolio/f06-house-eda/market_brief.md
```

## Scenario summary

[Three sentences: the nonprofit, the four neighborhoods, and the recommendation
you reached under the board's rule.]

## Decision rule I applied

| Rule | Value |
| --- | --- |
| Primary metric | Median `sale_price / area_sqft` per neighborhood |
| Eligibility threshold | At least 150 sales |
| Tie-break | If the top two are within 3%, choose the larger count |
| Outlier handling | Keep in main analysis; run a sensitivity check |

## Constraints

- Descriptive analysis only; no model and no causal claims.
- Repository data only; no external market or demographic data.
- At least three labeled figures saved under `outputs/`.
- Every number traceable to a cell in the submitted notebook.
- No addresses, names, or invented resident characteristics.

## Commands and seeds

```powershell
# [exact commands, including data generation]
```

| Item | Value |
| --- | --- |
| Data file and SHA-256 | [value] |
| Shape | [rows x columns] |
| pandas / NumPy / matplotlib | [versions] |
| Random seed (if any) | [value] |
| Working directory | [relative path, no username] |

## Required artifacts

| Artifact | Path | Present |
| --- | --- | --- |
| Executed notebook or script log | [path] | [yes/no] |
| Quality log | `quality_log.csv` | [yes/no] |
| Group summary | `group_summary.csv` | [yes/no] |
| Recommendation | `recommendation.json` | [yes/no] |
| Figures | `outputs/*.png` | [yes/no] |
| Brief | `market_brief.md` | [yes/no] |
| Reflection | `reflection.md` | [yes/no] |

## Group summary to fill in

| Neighborhood | Count | Median price | Mean price | Q1 | Q3 | IQR | Median price per sq ft | Eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| North | | | | | | | | |
| South | | | | | | | | |
| East | | | | | | | | |
| West | | | | | | | | |

## Report headings

```markdown
# F06 neighborhood market brief

## 1. Summary and recommendation
## 2. Data and provenance
## 3. Data quality
## 4. Distributions
## 5. Relationships
## 6. Group comparison
## 7. Decision
## 8. Sensitivity and anomalies
## 9. Limitations
## 10. Reproduction
```

## Validation checks

- [ ] 600 rows, 7 columns, unique rows, strictly positive prices.
- [ ] The recommendation is computed from the table, not hardcoded.
- [ ] The chosen neighborhood is eligible and in the top two on the metric.
- [ ] Three figures exist and are larger than zero bytes.
- [ ] Removing IQR-flagged rows does not silently replace the main result.

## Rubric reminder

| Dimension | Weight |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |

A dimension with no evidence scores zero. Full descriptors are in the
[lab brief](../../docs/lessons/f06-eda/lab.md#rubric).

## Privacy and ethics check

- [ ] The brief says the data is synthetic and not market advice.
- [ ] No invented demographics, schools, crime rates, or resident traits.
- [ ] No addresses, owner names, or listing identifiers.
- [ ] Language about lower-price neighborhoods is descriptive, not stigmatizing.
- [ ] No absolute personal paths or usernames in logs.
