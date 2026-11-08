# Model card

**Project:** [replace]  
**Model or system:** [replace: name, version, checksum]  
**Checkpoint:** 2 draft, 3 final

For P12, this file is also the **system card**: describe the policy, tools, and
approval gate rather than only a neural network. Keep the same sections.

## Intended use

- **Primary use:** [replace: the decision from `project-scope.md`]
- **Users:** [replace]
- **Input:** [replace: image, ticket text, task]
- **Output:** [replace: class and confidence, reply text, tool decision]
- **Operating conditions:** [replace: CPU, offline, single image, synthetic data]
- **Not intended for:** [replace: at least three prohibited or unsupported uses]

## Architecture

| Item | Value |
| --- | --- |
| Family | [replace: scratch CNN / LoRA adapter / scripted policy] |
| Parameters or rules | [replace: count, trainable count, or rule count] |
| Input size / context | [replace] |
| Output classes / actions | [replace] |
| Artifact size | [replace: bytes] |
| Licence | [replace: base model and adapter licences] |

## Training

| Item | Value |
| --- | --- |
| Data | [replace: dataset card version and digest] |
| Split | [replace: counts per split, grouped by source or template] |
| Objective | [replace: cross-entropy, masked token loss, none for scripted] |
| Seed | [replace] |
| Steps / epochs | [replace] |
| Batch size and learning rate | [replace] |
| Hardware | [replace: CPU model, threads; no GPU if none used] |
| Wall clock | [replace] |
| Selection rule | [replace: chosen on validation before test] |

## Evaluation

Report the frozen test result, with n and uncertainty. Do not paste training
numbers here.

| Metric | Value | n | 95% interval | Split |
| --- | ---: | ---: | --- | --- |
| [replace] | | | | test |

- Baseline: [replace: name and result on the same split]
- Per-class or per-slice summary: [replace]
- Calibration / abstention: [replace, or "not applicable"]
- Robustness: [replace: conditions and worst result]
- Failure cases: see [evaluation-report.md](evaluation-report.md)

## Limitations

- [replace: data limitation]
- [replace: method limitation]
- [replace: evaluation limitation (small n, single source, synthetic data)]
- [replace: condition that causes the worst measured failure]

## Risks and responsible use

- **Privacy:** [replace]
- **Fairness:** [replace: groups not represented, or "not applicable"]
- **Safety:** [replace: what happens when the output is wrong]
- **Misuse:** [replace: plausible abuse and the control that limits it]
- **Security boundaries:** [replace: for P12, the sandbox and approval gate]

## Ethical considerations

[replace: who could be harmed by a wrong output, how the system is monitored, and
what it must not be used for. For a system that acts, state the blast radius of
the most dangerous permitted action.]

## Version and contact

**Version:** [replace]  
**Date:** [replace]  
**Author:** [replace]  
**Evidence:** [replace: path to metrics.json and the release note]
