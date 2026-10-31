# Notebook guide template

!!! note "Template guidance"
    Copy this file to `docs/lessons/<module>/notebook.md`. The notebook itself
    lives in `notebooks/<area>/`. This page explains how to run it; it does not
    replace the notebook. Delete this box after copying.

# MNN guided notebook

```markdown
**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
```

**Notebook file:** `notebooks/[area]/[notebook-name].ipynb`  
**Hardware:** [label]  
**Time:** [estimated time]

[One sentence describing what the student will prove or produce.]

## What the notebook does

| Section | What you do | Evidence produced |
| --- | --- | --- |
| 1. [Section] | [Action] | [Artifact or output] |
| 2. [Section] | [Action] | [Artifact or output] |
| 3. [Section] | [Action] | [Artifact or output] |

## Run it locally

```powershell
cd [repository path]
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/[file].txt
python -m jupyter lab notebooks/[area]/[notebook-name].ipynb
```

Alternative: open the notebook in Visual Studio Code and select the project
interpreter as the kernel.

## Run it on Google Colab

1. Open [Google Colab](https://colab.research.google.com/).
2. Choose **File > Upload notebook** and select the notebook file.
3. Choose **Runtime > Change runtime type** and select [CPU/GPU].
4. Choose **Runtime > Run all**.
5. Download the required artifacts before the session ends.

[State which artifacts must be downloaded and where they appear.]

## What a healthy run looks like

| Check | Expected result | If it differs |
| --- | --- | --- |
| [Check] | [Value or `True`] | [What to inspect] |
| [Check] | [Value or `True`] | [What to inspect] |

[Note any result that is machine-dependent and should not be compared exactly.]

## Artifacts

| File | Commit or submit? | Notes |
| --- | --- | --- |
| [Report] | Yes | [Size and purpose] |
| [Model or plot] | No | Regenerate it |

## Troubleshooting

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| [Error] | [Cause] | [Action] |
| [Error] | [Cause] | [Action] |

## Submission checkpoint

- [ ] The notebook ran top-to-bottom in a fresh kernel.
- [ ] The required artifacts exist.
- [ ] The student can explain any skipped optional section.
- [ ] Personal paths and secrets are absent from the notebook output.

Next: the [lab brief](lab.md).

---

```markdown
**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
```
