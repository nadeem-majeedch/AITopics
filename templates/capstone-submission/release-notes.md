# Release notes

**Project:** [replace]  
**Version:** [replace: 0.1.0]  
**Date:** [replace]  
**Checkpoint:** 3

## Release decision

[replace: one paragraph. State "ship as an educational prototype", "portfolio
candidate", or "do not release", and the evidence that decides it. A "do not
release" decision is valid and must name what would change it.]

| Question | Answer |
| --- | --- |
| Release status | [replace: prototype / portfolio candidate / no release] |
| Deciding metric | [replace: value, n, interval] |
| Known failure that blocks wider use | [replace] |
| Who approved this decision | [replace] |

## What is included

- Code: [replace: commit or tag]
- Artifact: [replace: model/adapter name, checksum, size]
- Data: [replace: version and manifest digest]
- Evidence: [replace: outputs path]
- Documentation: the ten files in this package

## Changes in this version

| Type | Change | Evidence |
| --- | --- | --- |
| Added | [replace] | [replace: experiment id] |
| Changed | [replace] | [replace] |
| Fixed | [replace] | [replace] |
| Rejected | [replace: a change that did not help, with the result] | [replace] |

Do not delete rejected experiments from `experiments.csv`; list them here.

## Evidence summary

| Experiment | Claim | Result | n | Interval / caveat |
| --- | --- | ---: | ---: | --- |
| [replace] | [replace] | | | |

## Known limitations

1. [replace: data limitation]
2. [replace: evaluation limitation]
3. [replace: operating-condition limitation]
4. [replace: security or privacy residual risk]

## Monitoring

| Signal | Threshold | Action |
| --- | --- | --- |
| [replace: input drift, confidence drop, error rate] | [replace] | [replace] |

## Rollback

- Trigger: [replace: the measured condition that means the release is unsafe]
- Procedure: [replace: revert tag, restore artifact, disable path]
- Owner: [replace]

## Upgrade notes

[replace: what a user must change when moving from the previous version, or
"first release".]

## Verification

- [ ] Dataset check passed: [replace: command and result]
- [ ] Headline metric reproduced from a clean checkout: [replace: who and date]
- [ ] Threat review signed off: [replace: owner]
- [ ] No secrets, raw data, or personal data in the package
