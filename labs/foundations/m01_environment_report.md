# M01 environment report - submission template

Use this file as the starting point for the lab report required by the
[M01 lab brief](../../docs/lessons/m01-environment/lab.md). Replace every
bracketed prompt with your own evidence. Do not keep prompts you did not answer.

Save your completed copy outside the course repository, for example:

```text
portfolio/m01-environment/environment_report.md
```

## 1. Summary

[Two or three sentences: which environments you used, whether the notebook ran
in both, and the most important difference you found.]

## 2. Environment A - primary machine

| Field | Value |
| --- | --- |
| Machine and owner | [redact personal identifiers] |
| Operating system | [e.g., Windows 11 23H2, build 22631] |
| Python | [e.g., 3.12.10] |
| Environment tool | [venv / uv / Conda] |
| CPU | [model or core count] |
| RAM | [GiB] |
| GPU | [name or "none"] |
| VRAM | [GiB or "not applicable"] |
| Install command | [exact command] |

## 3. Environment B - second environment

| Field | Value |
| --- | --- |
| Environment type | [Google Colab / second machine / second venv] |
| Operating system | [value] |
| Python | [value] |
| CPU | [value] |
| RAM | [value] |
| GPU | [value or "none"] |
| VRAM | [value or "not applicable"] |
| Install command | [exact command] |

## 4. Comparison

| Item | Environment A | Environment B | Same? | Why it matters |
| --- | --- | --- | --- | --- |
| Python | [value] | [value] | [yes/no] | [interpretation] |
| NumPy | [value] | [value] | [yes/no] | [interpretation] |
| scikit-learn | [value] | [value] | [yes/no] | [interpretation] |
| CUDA available | [true/false] | [true/false] | [yes/no] | [interpretation] |
| Test accuracy | [value] | [value] | [yes/no] | [interpretation] |
| Matrix time | [value] | [value] | [yes/no] | [interpretation] |
| Failures or warnings | [value] | [value] | [yes/no] | [interpretation] |

### Interpretation

[Which differences are expected and harmless? Which could change a scientific
conclusion? Which environment will you use for M02, and why?]

## 5. Diagnosis

- **Failure or warning observed:** [exact message]
- **Command or cell that produced it:** [value]
- **Interpreter and package versions at the time:** [value]
- **Hypothesis:** [what you thought was wrong]
- **Test:** [what you changed or checked]
- **Result:** [what happened]
- **Fix or decision:** [what resolved it]
- **Prevention:** [what you will do next time]

If both environments ran perfectly, describe the non-destructive version
mismatch you created and diagnosed instead.

## 6. Reproduction instructions

```text
[Paste the exact commands that rebuild Environment A. Include the clone,
environment creation, activation, install, and notebook launch commands.]
```

Dependency lock file: [relative path, for example `requirements.lock`]

## 7. Limitations

[What could another student not reproduce from this report? Consider hardware,
private data, Colab quota, network access, or unrecorded settings.]

## 8. Privacy and safety check

- [ ] Usernames and personal paths removed from text and screenshots.
- [ ] Hostnames, IP addresses, and account identifiers removed.
- [ ] No tokens, passwords, or `.env` contents included.
- [ ] No dataset or model files included unless their license allows it.
- [ ] Colab sharing does not expose private Drive files.
