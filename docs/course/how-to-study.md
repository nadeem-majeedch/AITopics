# How to study

This course is self-paced, but it is not passive. Reading notebooks does not
produce skill. The method below is designed for working students, university
students with other courses, and independent learners.

## The core loop

For every module:

1. **Skim the theory page** to build a map of the topic.
2. **Run the guided notebook** exactly as provided. Do not change it yet.
3. **Re-run one cell at a time** and predict the output before executing.
4. **Break something on purpose.** Change a hyperparameter, remove a step, or
   corrupt the data, then explain what happened.
5. **Complete the independent lab** without copying the guided solution.
6. **Write a short reflection:** what worked, what failed, what you would do
   differently, and what evidence supports your claims.
7. **Store the artifact** in your portfolio with the module code.

## A sustainable weekly routine

A standard-pace learner spends about 13 hours per week. A possible structure:

| Day | Time | Activity |
| --- | --- | --- |
| Monday | 2 h | Read theory and write questions |
| Tuesday | 2 h | Guided notebook, first pass |
| Wednesday | 2 h | Guided notebook, experiments and notes |
| Thursday | 2 h | Lab planning and data checks |
| Friday | 2 h | Lab implementation |
| Saturday | 2 h | Evaluation, error analysis, report |
| Sunday | 1 h | Reflection, portfolio update, next-week plan |

Adjust the days, not the loop. Protect one uninterrupted block for the lab.

## Choose your environment deliberately

You can work in three ways:

| Mode | Best for | Trade-off |
| --- | --- | --- |
| Local Windows 11 + CPU | Levels 0-1, data work, RAG, small-model inference | Simple, but slow for training |
| Local Windows 11 + NVIDIA GPU | All modules if VRAM is sufficient | Fast, but driver/CUDA setup can break |
| Google Colab or Kaggle | GPU labs, quick experiments | Free, but sessions expire and storage is limited |

Pick a **primary** environment and a **backup**. For example, local CPU for
development and Colab for GPU training. Document both in your environment
report (M01).

!!! warning "Do not keep important work only in Colab"
    Colab sessions are ephemeral. Save notebooks to GitHub and datasets or
    checkpoints to Google Drive or a local disk. Treat `/content` as temporary.

## Notebook workflow

1. **Never edit the course notebook in place.** Open the notebook's page, choose
   **Download notebook (.ipynb)**, and save the file to your own work directory
   (or fork the repository and work from your fork).
2. **Run all cells from a clean kernel** before submitting or sharing.
3. **Record the environment:** Python version, package versions, hardware, and
   random seeds in the first cell.
4. **Keep outputs small.** Clear large logs and image dumps before committing.
5. **Annotate decisions** in Markdown cells: why this model, why this metric,
   what you expected, and what surprised you.
6. **Use relative paths** where possible, or a single configuration cell for
   paths so the notebook runs on Windows and Colab.
7. **Do not commit secrets.** Use environment variables or Colab secrets for
   API tokens.

## GPU budgeting

Free GPU time is limited. Use it like a budget:

- Develop and debug on CPU with a tiny subset first.
- Use the smallest model and dataset that can answer your question.
- Cache tokenized datasets and downloaded weights.
- Save checkpoints frequently.
- Prefer a short, well-monitored run over a long, unmonitored one.
- Write down the GPU type, memory, batch size, and runtime for every experiment.
- Stop sessions when finished.

A failed run that you can explain is more valuable than a successful run you
cannot reproduce.

## Debugging protocol

When something breaks, work in this order:

1. **Read the full error**, including the last frame and the shape/dtype.
2. **Reproduce minimally.** Reduce to one batch, one sample, or one row.
3. **Check the data**: paths, encodings, labels, missing values, duplicates,
   and train/validation leakage.
4. **Check the shapes and types** at every boundary.
5. **Check versions and device** (CPU vs GPU, dtype, library version).
6. **Set seeds** and test determinism.
7. **Search the exact error message** in official documentation and issue
   trackers.
8. **Ask for help with a minimal reproduction**, not a screenshot of a stack
   trace.

Keep a `DEBUG.md` in your lab folder. It becomes evidence of engineering
judgment.

## Asking for help

Use the repository's GitHub Issues for course errors and ambiguities. Include:

- Module code and page or notebook name.
- What you expected and what happened.
- The exact command, package versions, and hardware.
- A minimal reproduction or a link to a notebook.
- What you already tried.

Do not post datasets that you do not have permission to share, personal data,
or API keys.

## Academic integrity and AI assistants

- **Allowed:** using AI assistants to explain concepts, review your code,
  generate test cases, and debug errors.
- **Not allowed:** submitting AI-generated work as your own without disclosure,
  copying another learner's lab, or fabricating results.
- **Required:** disclose substantial AI assistance in your lab reflection,
  including the tool and what it helped with.
- **Always verify:** AI assistants hallucinate APIs, metrics, and citations.
  Run the code, check the documentation, and validate claims against your data.

The goal is capability, not completion. A lab you cannot explain is not a lab
you have learned.

## Notes and portfolio

Keep a single portfolio repository with this structure:

```text
portfolio/
  README.md
  m01-environment/
    notebook.ipynb
    report.md
  m02-ml-foundations/
    ...
  capstone/
    ...
```

For each artifact, record:

- Module code and title.
- Problem and dataset.
- Method and key decisions.
- Metrics and error analysis.
- Hardware and runtime.
- Limitations and ethical considerations.
- What you would do next.

At the end, your portfolio is your evidence. Recruiters and supervisors can
inspect it without trusting a grade.

## Time management and wellbeing

- **Plan 20% buffer.** Labs often take longer than estimated, especially the
  first time you use a new library.
- **Stop at a clean boundary.** Save your notebook and write one sentence about
  the next step before you leave.
- **Take breaks from the screen.** Long GPU waits are not study time.
- **Do not compare your first lab to someone else's polished capstone.**
- **Ask for help early.** Being stuck for a day is normal; being stuck for a
  week is a process problem.

## Self-assessment before moving on

You are ready for the next module when you can:

- Explain the module's core idea without reading your notes.
- Reproduce the guided result from a clean environment.
- Complete the independent lab within the stated constraints.
- Identify at least two failure modes and how you would detect them.
- State the limitations of your result honestly.

If not, repeat the lab with a smaller scope. Depth beats speed.
