# Level 5 - Production and capstone

**Modules:** M16-M17 | **Hours:** 60 | **Hardware:** CPU-only to project-dependent

Level 5 turns a working prototype into a defensible system: evaluated, tested,
secured, packaged, deployed, monitored, and documented. The capstone combines
your path modules into a portfolio centerpiece.

!!! note "Level outcome"
    You can defend an AI system's quality, security, cost, and limitations, and
    deliver a reproducible capstone with a report, cards, demo, and rollback
    plan.

## Readiness check

- Do you have at least one working model or application from your path?
- Can you write automated tests and package a Python application?
- Can you explain the difference between offline evaluation and production
  monitoring?
- Have you documented a dataset or model with intended use and limitations?

If not, complete the relevant path modules and M05 first.

---

## M16 - Evaluation, security, responsible AI, and deployment {#m16}

**Level 5 | 20 hours | CPU-only | Prerequisite: at least one applied path module**

### Learning objectives

By the end of this module, you can:

1. Write an evaluation plan before building, with metrics, slices, and failure
   criteria.
2. Build held-out test sets and report uncertainty, not just point estimates.
3. Evaluate generative systems with task metrics, rubric scoring, and human
   review, and explain the limits of LLM-as-judge.
4. Red-team a system using the OWASP Top 10 for LLM applications as a checklist.
5. Audit privacy, bias, licensing, and data provenance.
6. Write model and system cards that state intended use and limitations.
7. Package a model as a tested API and container.
8. Plan monitoring, drift detection, incident response, and rollback.
9. Estimate and control inference cost.

### Prerequisites

- At least one applied module: M07-M16.
- Basic Python packaging and command-line skills.
- No GPU required for the core lab.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 4 h | 7 h | 8 h | 1 h | 20 h |

### Required theory

- Evaluation plans, pre-registration, and avoiding test-set tuning.
- Held-out data, slices, confidence intervals, and statistical significance.
- Task metrics vs human judgment vs model judgment.
- LLM-as-judge biases and calibration; when human review is required.
- Red teaming and adversarial testing.
- OWASP Top 10 for LLM Applications: prompt injection, insecure output handling,
  training-data poisoning, model denial of service, supply-chain risks, sensitive
  information disclosure, insecure plugin design, excessive agency, overreliance,
  and model theft.
- Privacy: data minimization, retention, access control, and deletion.
- Bias and fairness: measurement, slices, and mitigation limits.
- Licensing and acceptable-use policies for models and data.
- Model cards and system cards.
- API design: input validation, timeouts, rate limits, and structured errors.
- Packaging with FastAPI, Docker, and dependency pinning.
- Serving options: Transformers, vLLM, Ollama, and managed endpoints.
- Monitoring: latency, errors, quality proxies, drift, and feedback.
- Incident response, rollback, and change management.
- Cost modeling: tokens, GPU time, storage, and egress.

### Guided notebook

**Planned path:** `notebooks/production/m16_production.ipynb`

The notebook will:

1. Take a small model or RAG pipeline from an earlier module.
2. Write an evaluation plan with metrics, slices, and failure criteria.
3. Build a FastAPI service with input validation and structured errors.
4. Add tests for normal, edge, and malicious inputs.
5. Containerize the service and run it locally.
6. Measure latency, throughput, and memory.
7. Add structured logs and a health endpoint.
8. Run a red-team checklist and record findings.
9. Draft a model card and a rollback plan.

**Hardware:** CPU-only for small models and RAG; a GPU is optional for serving
larger models.

### Independent lab

**Brief:** Deploy and defend a system you built earlier in the course.

Required evidence:

- Evaluation plan and results on a held-out set, including slices and uncertainty.
- Automated tests: unit, integration, and at least five adversarial inputs.
- A running API and container, or a reproducible local deployment script.
- Input validation, rate limits, timeouts, and structured errors.
- Security review covering the OWASP LLM risks relevant to your system.
- Privacy and data-flow diagram.
- Model or system card with intended use, metrics, and limitations.
- Monitoring plan: what is measured, alert thresholds, and who responds.
- Incident response and rollback procedure.
- Cost estimate for a stated usage level.

**Constraints:** No real secrets or personal data. Do not expose an unauthenticated
public endpoint with write access. Document residual risk honestly.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- Evaluation was planned before the final run.
- At least one security finding is documented with a mitigation.
- The deployment is reproducible from a clean environment.
- Monitoring and rollback are concrete, not aspirational.
- Limitations are stated without marketing language.

### Deliverables

- Evaluation report with slices and uncertainty.
- Test suite and adversarial test results.
- Deployed API or reproducible deployment package.
- Security and privacy review.
- Model/system card.
- Monitoring and rollback plan.
- Cost estimate.

### Next step

M17 - Integrated capstone.

### Risks and notes

- **A public demo is not a deployment.** Authentication, rate limits, and
  monitoring are part of the system.
- **LLM judges are biased.** Validate them against human labels.
- **Security is not a checklist.** Use the checklist to find risks, then reason
  about your specific system.
- **Cost surprises:** token budgets, GPU idle time, and egress can dominate.

---

## M17 - Integrated capstone {#m17}

**Level 5 | 40 hours | Hardware depends on project | Prerequisites: path modules and M16**

### Learning objectives

By the end of this module, you can:

1. Define a bounded AI problem with users, success criteria, and non-goals.
2. Audit data for provenance, license, consent, bias, and fitness.
3. Establish a baseline and an evaluation plan before the final build.
4. Build and iterate on a system using evidence, not intuition alone.
5. Evaluate with held-out data, slices, uncertainty, and failure analysis.
6. Secure the system and document residual risk.
7. Deliver a reproducible repository, report, cards, demo, and presentation.
8. Reflect critically on what you would change.

### Prerequisites

- M00-M05.
- The modules in your chosen [learning path](../course/learning-paths.md).
- M16 before final submission.

### Study time

| Phase | Hours |
| --- | --- |
| Proposal and scope | 3 |
| Data audit | 5 |
| Baseline and evaluation harness | 5 |
| Build and iterate | 12 |
| Evaluation and error analysis | 6 |
| Security and ethics review | 3 |
| Documentation | 4 |
| Demo and presentation | 2 |
| **Total** | **40** |

### Required theory

- Problem framing and scope control.
- Baseline design and comparison fairness.
- Evaluation plans and failure criteria.
- Reproducibility and documentation.
- Risk analysis and responsible release.
- Technical writing and demonstration.

### Project options

Full briefs, data guidance, risks, and milestones are in
[Capstone projects](../course/projects.md). Options:

- **A:** Domain small-language-model assistant with RAG.
- **B:** Visual inspection or classification system.
- **C:** Privacy-preserving video analytics.
- **D:** Speech and audio assistant.
- **E:** Tool-using AI agent.

You may propose another option if it meets the same standards and is approved
before data collection.

### Guided work

There is no guided notebook for the capstone. Instead, you follow the milestones:

1. **Proposal:** one page with users, problem, data plan, risks, and non-goals.
2. **Data audit:** dataset card, license, consent, and sample review.
3. **Baseline:** simplest credible system and evaluation harness.
4. **Midpoint review:** working prototype and first honest metrics.
5. **Evaluation:** held-out results, slices, failure taxonomy, uncertainty.
6. **Security and ethics:** threat model and privacy review.
7. **Final package:** repository, report, cards, demo, and presentation.

### Assessment criteria

The capstone is assessed with the
[capstone rubric](../course/assessments.md#capstone-rubric), not the standard
module split. Weights:

| Criterion | Weight |
| --- | --- |
| Problem framing and scope | 10% |
| Data quality, licensing, and ethics | 15% |
| Technical implementation | 25% |
| Evaluation and error analysis | 20% |
| Reproducibility and documentation | 15% |
| Demo and communication | 10% |
| Reflection and next steps | 5% |

A capstone with unsupported performance or safety claims cannot exceed
"Approaching" on evaluation, regardless of demo quality.

### Deliverables

- Capstone repository with reproducible environment and data scripts.
- Proposal and milestone notes.
- Dataset card.
- Model or system card.
- Evaluation report with slices and failure taxonomy.
- Security and privacy review.
- Working demo.
- 8-12 page final report.
- 8-10 minute presentation.
- Reflection.

### Next step

After the capstone:

- Publish a sanitized portfolio version with licenses and data removed.
- Write a blog post or technical report for a student venue.
- Contribute a lab or dataset card to this course.
- Continue with advanced study in your chosen area: distributed training,
  reinforcement learning, multimodal models, or production MLOps.

### Risks and notes

- **Scope creep** is the main cause of unfinished capstones. Cut features, not
  evaluation.
- **Data access delays:** secure permissions before the build phase.
- **Compute limits:** design for the hardware you actually have.
- **Ethics:** if the project drifts toward surveillance, identity inference, or
  harm, stop and consult the instructor.
- **Reproducibility:** a reviewer must be able to run your demo without your
  laptop.

---

## Level 5 completion checklist

- [ ] I wrote an evaluation plan before the final build.
- [ ] I tested security and privacy risks.
- [ ] I deployed or packaged a reproducible system.
- [ ] I wrote a model/system card and a monitoring plan.
- [ ] I completed a capstone proposal and milestones.
- [ ] I evaluated on held-out data with slices and uncertainty.
- [ ] I delivered a report, demo, and presentation.
- [ ] I documented limitations and next steps.

## Course completion

You have completed the full program when you have:

- Portfolio artifacts for the modules in your path.
- A capstone that meets the rubric.
- A written reflection on your growth and remaining gaps.
- A sanitized public portfolio you can share.

Return to the [roadmap](../course/roadmap.md) to review milestones, or explore
another [learning path](../course/learning-paths.md).
