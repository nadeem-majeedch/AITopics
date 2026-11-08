# Dataset card

**Project:** [replace]  
**Dataset:** [replace: name and version]  
**Checkpoint:** 1

## Origin and provenance

| Field | Value |
| --- | --- |
| Origin | [replace: generated / collected / downloaded] |
| Generator or source | [replace: script path or URL] |
| Version | [replace: e.g. objects_p06 v1.0.0] |
| Manifest | [replace: path to manifest.json and its digest, or "not applicable"] |
| Created | [replace: date] |
| Licence | [replace: exact licence string and URL] |
| Attribution | [replace] |
| Personal data | [replace: none / describe consent, retention, and access] |

## Size and labels

| Split | Images or rows | Class A | Class B | Class C | Class D |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | [replace] | | | | |
| validation | [replace] | | | | |
| test | [replace] | | | | |
| **total** | | | | | |

- **Unit:** [replace: one image of one object / one support ticket / one task]
- **Label definition:** [replace: one paragraph per class, including a boundary case]
- **Label source:** [replace: generated rule / human label / dataset annotation]
- **Inter-rater or rule agreement:** [replace, or "not measured"]

## Collection or generation

[replace: the exact command, seed, and parameters. For a generated set, state
whether regenerating produces byte-identical files and how you checked. For a
collected set, describe the device, conditions, and selection process.]

```bash
[replace: generation or download command]
```

## Preprocessing

| Step | Setting | Applied to |
| --- | --- | --- |
| Resize | [replace] | [replace] |
| Normalisation | [replace] | [replace] |
| Augmentation | [replace: only train] | [replace] |
| Tokenisation | [replace] | [replace] |
| Other | [replace] | [replace] |

Preprocessing is fitted on training data only. State anything fitted on the full
set and why that does not leak test information.

## Splits and leakage

- Split method: [replace: grouped by source / template / task family]
- Source overlap between splits: [replace: none, with the check command]
- Near-duplicate check: [replace: method and result]
- Test set opened for final numbers: [replace: once, on date]

## Privacy and ethics

- Personal data present: [replace: no / describe]
- Consent and retention: [replace]
- Sensitive attributes: [replace: none / describe why they are needed and how they are protected]
- Re-identification risk: [replace]
- Prohibited uses: [replace]

## Limitations and known gaps

- [replace: e.g. "synthetic images come from one renderer and do not represent photographs"]
- [replace: e.g. "36 test images per class support a coarse interval, not a precise estimate"]
- [replace: e.g. "one product template dominates the training replies"]
- [replace: known label noise or ambiguous cases, with counts]

## Checkpoint 1 gate

- [ ] Licence and URL are exact strings.
- [ ] Counts per class per split are recorded, not estimated.
- [ ] The split unit and leakage check are described.
- [ ] Personal data is either absent or covered by consent and retention.
- [ ] At least three limitations are specific to this dataset.
