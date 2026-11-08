# Human student pilot protocol

**Status: not yet conducted.** This protocol prepares a human usability pilot for
the first release candidate. It does not contain student results and must not be
cited as evidence that a student completed the course.

**Protocol version:** 1.0  
**Prepared:** 2026-11-08  
**Applies to:** `v0.1.0-rc.1`  
**Related:** [v1 release-candidate checklist](v1-release-candidate-checklist.md)

## 1. Purpose

Test whether a student who has **not worked on this repository** can discover the
course, follow the beginner path, run a notebook, complete one lab, find an
assessment and capstone, understand submission requirements, and find help
without the author taking over the keyboard.

This is a usability and onboarding pilot, not a learning-outcomes study. One
participant is enough to expose navigation and setup problems; it is not enough
to claim that the course is effective for a population.

## 2. Participant and ethics

- Recruit **one student** who has not seen the repository, its lessons, or its
  internal docs.
- The participant should meet the published beginner prerequisites: basic Python,
  a terminal, and high-school algebra. Do not recruit an expert who can silently
  fill every gap.
- Use a participant code (for example `PILOT-01`), not a name, in the record.
- Obtain consent to observe the session and retain anonymised notes. Do not
  record audio, video, screen, or personal data unless the participant gives
  separate written consent.
- The author or a maintainer may observe but must not guide. The observer may
  answer only safety, consent, or "where do I type this command" questions after
  the participant has tried the published instructions.
- Stop if the participant is uncomfortable, the session exceeds the agreed time,
  or a task would require installing untrusted software or exposing credentials.

## 3. Session shape

Use two sessions so the pilot measures discovery separately from lab effort.

| Session | Time box | Tasks |
| --- | ---: | --- |
| A: discover and run | 60–90 minutes | 1–5 |
| B: complete and plan | 120–150 minutes | 6–10 |

The F01 lab is published as about two hours of work. Do not shorten it into a
demo; the point is to see whether the published brief and starter template are
usable without the author's explanation.

Record elapsed time per task, including setup and recovery. A task that needs an
intervention is still a result: mark it **completed with intervention** and
record exactly what was supplied.

## 4. Tasks and completion criteria

### Task 1 — Discover the course

**Start:** repository URL or the course landing page, with no other links.

**Ask:** "Find out what this course is, who it is for, and where you would start."

**Complete when the participant:**

- states the course purpose and audience in their own words;
- finds the "Start with F01" or equivalent beginner entry point;
- finds the course site and the repository.

**Record:** first click, time to the start point, any term that was unfamiliar.

### Task 2 — Understand prerequisites

**Start:** the landing page or roadmap.

**Ask:** "Decide whether you are ready to start, and what you would need first."

**Complete when the participant finds:**

- the knowledge prerequisites;
- the hardware and software expectations;
- at least one readiness action or self-check.

**Record:** whether the distinction between "CPU core", "GPU recommended", and
"GPU required" was understood.

### Task 3 — Follow the roadmap

**Ask:** "Choose a study schedule and explain what you would do in the first two
weeks."

**Complete when the participant:**

- finds the roadmap or a learning path;
- identifies the first modules and an approximate weekly commitment;
- follows a working link to the first lesson.

**Record:** whether the number of paths or schedule options caused hesitation.

### Task 4 — Open a beginner lesson

**Start:** the link the participant chose.

**Ask:** "Find the lesson, the guided notebook, the lab, and the assessment for
this module."

**Complete when the participant reaches all four F01 pages and can explain how
they relate.

**Record:** broken links, unclear labels, and any page that looked like a dead
end.

### Task 5 — Run a notebook

**Start:** `notebooks/foundations/f01_python_ai.ipynb` and the published setup
instructions.

**Ask:** "Run the notebook from a clean environment and show me the last output."

**Complete when:**

- the notebook opens in Jupyter, VS Code, Colab, or the documented environment;
- the code cells execute top to bottom;
- the participant can state the Python version and where the notebook ran.

**Record:** install steps that failed, missing packages, kernel confusion, and
whether the participant found the troubleshooting or setup help.

### Task 6 — Complete the F01 lab

**Start:** `labs/foundations/f01_python_toolkit.md` and the F01 lab brief.

**Ask:** "Complete the lab using the published brief and starter template. Keep
your work outside the course repository."

**Complete when the participant:**

- creates the required workspace and `data/pilot_runs.csv`;
- produces a runnable `toolkit.py` and `selfcheck.py`;
- reports seven valid runs and two rejected rows;
- produces the required summary artifacts and a memo;
- can run the self-check from a clean output state.

**Record:** the first failing check, the exact error text, whether the rubric or
self-check helped, and the time to the first working `selfcheck.py`. A partial
lab is recorded as partial; do not complete it for the participant.

### Task 7 — Locate an assessment

**Ask:** "Find how this module is assessed and what evidence you would submit."

**Complete when the participant finds the F01 assessment, the weighting, and the
self-scoring or submission instructions.

**Record:** whether assessment banks and solutions are distinguishable from
graded work.

### Task 8 — Select a capstone

**Start:** `docs/course/projects/index.md`.

**Ask:** "Choose one capstone that fits your interests and available hardware,
and explain why."

**Complete when the participant:**

- compares at least two project briefs;
- identifies hardware, data, and licensing expectations;
- names the project they would choose and one trade-off.

**Record:** whether the hardware labels and project scope were clear enough to
choose without asking.

### Task 9 — Understand submission requirements

**Start:** the chosen project brief.

**Ask:** "List the files you would submit and the checkpoints you would need to
pass."

**Complete when the participant finds the ten-file submission package, the three
capstone checkpoints, and the report template.

**Record:** whether the participant noticed that the course is self-study and
whether the "second person" or "marker" wording implied an unavailable grader.

### Task 10 — Find help

**Ask:** "You are stuck on an installation error. Find the route you would use
for help, and tell me what information you would include."

**Complete when the participant finds at least two of:**

- the FAQ;
- the troubleshooting page;
- the setup/environment guide;
- the repository issue tracker or feedback route.

**Record:** whether the route was findable from the page where the error occurred,
not only from the repository root.

## 5. Observation record

Complete one row per task. Use `PASS`, `PASS WITH INTERVENTION`, `PARTIAL`, or
`BLOCKED`. Do not convert these qualitative results into a score.

| Task | Result | Time | What the participant did | Confusion or failure | Intervention | Evidence |
| --- | --- | ---: | --- | --- | --- | --- |
| 1. Discover course |  |  |  |  |  |  |
| 2. Prerequisites |  |  |  |  |  |  |
| 3. Roadmap |  |  |  |  |  |  |
| 4. Beginner lesson |  |  |  |  |  |  |
| 5. Run notebook |  |  |  |  |  |  |
| 6. Complete lab |  |  |  |  |  |  |
| 7. Assessment |  |  |  |  |  |  |
| 8. Capstone choice |  |  |  |  |  |  |
| 9. Submission |  |  |  |  |  |  |
| 10. Find help |  |  |  |  |  |  |

### Environment record

| Field | Value |
| --- | --- |
| Participant code |  |
| Date and timezone |  |
| Operating system and version |  |
| Python version |  |
| Hardware / RAM |  |
| Browser |  |
| Notebook runner | JupyterLab / VS Code / Colab / other |
| Network or account constraints |  |
| Session A duration |  |
| Session B duration |  |

## 6. Feedback capture

Ask these questions after each session, without defending the material:

1. What did you expect the first page to tell you that it did not?
2. Where did you have to guess what a term meant?
3. Which instruction was the first one that did not match what you saw?
4. What did you do when the notebook or lab failed?
5. Was the difference between lesson, notebook, lab, assessment, and capstone
   clear? If not, where did it break down?
6. Did any page make a claim about hardware, data, or results that you could not
   verify?
7. What would have made the first 30 minutes easier?
8. Would you continue to the next module without help? Why or why not?

Record direct quotes only with permission. Paraphrase otherwise.

## 7. Remediation tracking

Create one row for every actionable finding. A finding is not closed merely
because the observer explained it during the session.

| ID | Finding | Severity | Evidence | Proposed fix | Owner | Status | Re-test |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PILOT-01-01 |  |  |  |  |  | Open |  |

Severity:

- **Critical:** blocks a beginner from starting, running the notebook, or finding
  the lab; or exposes personal data, credentials, or an unsafe instruction.
- **Major:** causes a wrong turn, a missing prerequisite, or a materially
  misleading claim.
- **Minor:** costs time or confidence without blocking the task.
- **Editorial:** spelling, formatting, or a broken non-essential link.

Close a finding only after the fix is in the working tree and a second pass, with
the same participant or a new participant, confirms the task is no longer
blocked. Record the re-test date and result.

## 8. Pilot completion criteria

The pilot is complete when:

- [ ] consent and scope were recorded;
- [ ] both sessions were attempted within the time boxes;
- [ ] all ten tasks have a result and elapsed time;
- [ ] the participant's environment and notebook path are recorded;
- [ ] every confusion has a remediation row with an owner;
- [ ] no participant name or personal data appears in the record;
- [ ] critical findings are fixed or explicitly accepted by the instructor;
- [ ] the release notes state whether the human pilot passed, partially passed,
      or was not completed.

A completed pilot is **not** a claim that the course improves learning outcomes.
It is evidence that one new student could navigate and execute the beginner path.

## 9. Release decision use

| Pilot outcome | Release effect |
| --- | --- |
| No critical findings; all tasks pass or pass with minor intervention | Supports an `rc` release note that says one human beginner completed the path |
| Critical or repeated major findings | Fix and re-test; do not call the course student-validated |
| Pilot not completed | Keep the human-pilot item open; do not imply student validation |
| Participant needed author intervention on more than two core tasks | Treat as a major onboarding defect until re-tested |

The instructor decides whether a deferred pilot is acceptable for a release
candidate. A deferred pilot must be stated plainly in the release notes and must
not be described as a pass.
