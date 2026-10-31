# F01 - Python essentials for AI {#f01}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 0 - Orientation (runs before M01) |
| **Study time** | 8 hours: 2 h reading, 3 h guided notebook, 2 h lab, 1 h assessment |
| **Hardware** | CPU-only. Standard library only; no GPU, no model downloads. |
| **Prerequisites** | Basic computer use: you can open a terminal, create a folder, and edit a text file. No AI, statistics, or advanced Python needed. |
| **You will produce** | An executed notebook, `outputs/run_log.json`, `outputs/run_log.csv`, a tested toolkit module, and a one-page model recommendation memo |

## Why this module exists

A study group runs three classifiers on the same 50 test emails. One student
writes `correct / total` where both values are integers and reports an accuracy
of `0`. Another writes the results in a chat message, so nobody can tell which
number came from which model. A third changes the code until the number looks
right and cannot explain what changed.

None of these failures is about machine learning. They are about the small
Python decisions that make a result trustworthy or worthless: choosing the right
container, validating inputs, writing results to a file, and separating "this
model is more accurate" from "this model is worth the extra latency."

This module builds the toolkit you will reuse in every later notebook: typed
records, checked functions, and a run log that survives the notebook session.
Everything here runs on the Python standard library, so it works on any machine
that has Python 3.10 or newer.

## Learning objectives

By the end of this module, you can:

1. Predict the type and value of a simple Python expression, including integer
   division and floating-point rounding, and convert types deliberately.
2. Choose among `list`, `tuple`, `dict`, and `set` for a stated task and explain
   the trade-off in one sentence.
3. Write a function with an explicit contract that raises `ValueError` for
   impossible inputs, and explain when to use an assertion instead.
4. Transform and filter a list of records with a comprehension, without mutating
   the original list.
5. Define a frozen dataclass that rejects invalid metric values at construction
   time.
6. Parse numeric values from untrusted text, returning `None` instead of
   crashing, and count how many values were rejected.
7. Write and read back a JSON and a CSV run log, verifying that the round trip
   preserved the record count and a known value, then compare runs on accuracy
   and latency and state which one you would ship.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| Python 3.10 or newer | The notebook uses `X \| None` type syntax and modern `dataclasses` |
| A terminal that can run `python --version` | You will launch Jupyter or run the notebook from a terminal |
| A plain text editor | You will read and edit `.py` and `.md` files, not only notebook cells |
| About 50 MB of free disk | The notebook writes two small output files |
| No prior AI course | This unit assumes no machine learning background at all |

If Python is not installed yet, install it from the official python.org
installer and keep the "Add python.exe to PATH" option enabled. You do not need
NumPy, pandas, or PyTorch for this unit. If installation is blocked, Google Colab
provides a Python runtime in the browser and the notebook runs there too, because
it imports only the standard library.

## The concepts you need

### 1. Values, types, and the cost of a silent conversion

Python is **dynamically typed**: a variable name can point to an integer now and
a string later. The interpreter infers the type from the value, which makes
experiments fast and pipelines fragile.

Three behaviors cause most beginner errors:

| Expression | Result | Why it surprises people |
| --- | --- | --- |
| `41 / 50` | `0.82` | `/` always returns a float |
| `41 // 50` | `0` | `//` is floor division; the remainder is discarded |
| `0.1 + 0.2` | `0.30000000000000004` | Binary floating point cannot represent most decimals exactly |
| `0.1 + 0.2 == 0.3` | `False` | Exact equality on floats is unreliable |
| `math.isclose(0.1 + 0.2, 0.3)` | `True` | Compares within a tolerance |

An **accuracy** is the fraction of predictions that are correct, a number between
0 and 1. If a model answers 41 of 50 items correctly, its accuracy is
`41 / 50 = 0.82`.

```python
correct, total = 41, 50
accuracy = correct / total
print(accuracy, type(accuracy))   # 0.82 <class 'float'>
```

Print the type when a number looks wrong. `0` where you expected `0.82` is almost
always floor division or a string that was never converted.

Rules that prevent most of these bugs:

- Use `/` for proportions and `//` only when you truly want whole groups.
- Compare floats with `math.isclose(a, b)` or `round(a, 3) == round(b, 3)`.
- Convert input at the boundary, once, and fail loudly if the conversion is
  impossible. Do not sprinkle `float(...)` through the analysis.

### 2. Collections: choose the shape that matches the question

A **collection** holds several values. Python's four built-in collections have
different guarantees, and picking the wrong one creates either bugs or slow code.

| Collection | Ordered? | Duplicates? | Lookup by | Use it for |
| --- | --- | --- | --- | --- |
| `list` | yes | yes | position | predictions in order, rows you append |
| `tuple` | yes | yes | position | a fixed record such as `(accuracy, latency)` |
| `dict` | insertion order | keys no | key | metrics by model name, JSON payloads |
| `set` | no | no | membership | unique labels, "have I seen this?" checks |

A **record** is one observation with several named fields. The most common shape
for small experiment logs is a list of dictionaries:

```python
records = [
    {"model": "baseline", "correct": 30, "total": 50, "latency_ms": 2.1},
    {"model": "logistic", "correct": 41, "total": 50, "latency_ms": 3.4},
    {"model": "tree", "correct": 43, "total": 50, "latency_ms": 4.8},
]
```

Two useful derivations from that list:

- `[row["model"] for row in records]` gives the labels in order.
- `{row["latency_ms"] for row in records}` gives unique latencies, which is a
  fast way to spot duplicated measurements.

Do not use a `set` when order matters, and do not use a `list` when you need to
look up a value by name thousands of times.

### 3. Functions with a contract and validation

A **contract** is what a function promises: what it accepts, what it returns, and
what it does when the input is invalid. Write the contract in the signature and
enforce it in the body.

```python
def accuracy(correct: int, total: int) -> float:
    if total <= 0:
        raise ValueError("total must be positive")
    if not 0 <= correct <= total:
        raise ValueError("correct must be between 0 and total")
    return correct / total
```

The **docstring** is optional here; the type hints and the guards carry the
contract. Callers can now rely on three facts: the result is a `float`, it lies
in `[0, 1]`, and bad input produces an exception rather than a plausible-looking
wrong number.

A second example, **mean absolute error (MAE)** — the average distance between
predicted and actual values, in the units of the target:

```python
def mae(actual: list[float], predicted: list[float]) -> float:
    if len(actual) != len(predicted):
        raise ValueError("actual and predicted must have the same length")
    return sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)

mae([10, 20, 30], [12, 18, 33])   # 7 / 3 = 2.333...
```

Worked example: the errors are `2`, `2`, and `3`. Their sum is `7`, the count is
`3`, so the MAE is `7 / 3 = 2.333`. The value is in target units, so "2.33 points
off on average" is a sentence a reader can act on.

**Assertions versus exceptions** — they are not interchangeable:

| Mechanism | Use it when | Example |
| --- | --- | --- |
| `raise ValueError` | Input comes from a user, file, or API and may be wrong | `total <= 0` |
| `assert condition` | You are checking your own logic while developing | `assert df.shape == (400, 9)` |
| `try / except` | You can recover and want to keep the run alive | Parsing `"n/a"` as `None` |

Python can run with assertions disabled (`python -O`), so never use `assert` to
validate data you do not control.

### 4. Comprehensions and generator expressions

A **comprehension** builds a new collection from an iterable in one expression.
A **generator expression** produces values lazily and is what you want when you
only feed them to `sum`, `max`, or `any`.

```python
scored = [(row["model"], accuracy(row["correct"], row["total"]))
          for row in records]
strong = [name for name, value in scored if value > 0.80]
# [('baseline', 0.6), ('logistic', 0.82), ('tree', 0.86)]
# ['logistic', 'tree']
```

The same logic as a loop is four lines longer but easier to debug with a
breakpoint. Use a comprehension for a single transform-and-filter step, and a
named function when the body needs three conditions. Do not nest three
comprehensions: nobody, including you next week, will read it.

### 5. Dataclasses as records with invariants

A **dataclass** is a class that generates `__init__`, `__repr__`, and `__eq__`
for you from annotated fields. An **invariant** is a rule that must always hold,
such as "accuracy is between 0 and 1".

```python
@dataclass(frozen=True)
class Run:
    model: str
    accuracy: float
    latency_ms: float
    params: int

    def __post_init__(self):
        if not self.model.strip():
            raise ValueError("model name cannot be empty")
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError("accuracy must be in [0, 1]")
        if self.latency_ms <= 0 or self.params < 0:
            raise ValueError("latency must be positive and params non-negative")
```

- `frozen=True` makes the instance read-only, so a later cell cannot silently
  overwrite a recorded accuracy.
- `__post_init__` runs after construction and is the correct place to enforce
  invariants.
- An invalid run now fails at the line where it was created, not three cells
  later inside a mean.

`asdict(run)` converts a run to a plain dictionary, which is exactly what
`json.dumps` needs. That single method removes most serialization boilerplate.

Typical parameter counts for the three runs in the notebook:

| Model | Correct / 50 | Accuracy | Latency (ms) | Parameters |
| --- | --- | --- | --- | --- |
| baseline | 30 | 0.60 | 2.1 | 0 |
| logistic | 41 | 0.82 | 3.4 | 13 |
| tree | 43 | 0.86 | 4.8 | 1,201 |

### 6. Untrusted input: parse, do not crash

Data arrives as text: CSV cells, form fields, API responses. A **parser** converts
text into a typed value or a clear failure. Two rules make parsers safe:

1. Return a distinguishable "missing" value (`None`) rather than `0`, because
   `0` is a valid measurement.
2. Report what was rejected, so a silent data loss becomes visible.

```python
def parse_float(raw, field: str) -> float | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        print(f"warning: {field}={raw!r} is not numeric; using None")
        return None
```

Catching only `TypeError` and `ValueError` matters. A bare `except:` also swallows
`KeyboardInterrupt` and typos such as a misspelled variable name, which turns a
crash into a wrong result.

### 7. Persisting evidence: JSON and CSV

A result that exists only in a notebook output is hard to compare, easy to lose,
and impossible to diff. Two formats cover most foundation work:

| Format | Strength | Weakness | Use it for |
| --- | --- | --- | --- |
| JSON | Nested structure, explicit types, seed and metadata | Not readable in a spreadsheet | Run logs, summaries, configs |
| CSV | Opens in Excel, one row per record | Flat only; types are lost on reload | Per-run tables, per-row data |

The notebook writes one payload to both formats, then reads each file back and
checks it:

```python
payload = {
    "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED,
    "runs": [asdict(run) for run in runs],
}
```

A **round trip** means write, read, and compare. Check the record count and at
least one known value; a file that exists is not evidence that it is correct.
CSV reloads everything as text, so `reloaded["params"][0]` is `"0"`, not `0`. That
is a property of the format, not a bug; convert after reading when you need
numeric types.

The notebook asserts that the JSON reload has `seed == 42` and three runs, and
that the CSV reload has three rows. Those two assertions are the minimum standard
for any artifact you submit.

## Guided walkthrough

The full practical is the [guided notebook](notebook.md). It runs in eight
sections, each proving one skill:

1. **Values and types** — prints the interpreter version and confirms that
   `accuracy(41, 50)` is a float in `[0, 1]`. Proves that you can predict types.
2. **Collections** — builds the three-run record list and extracts labels and
   unique latencies. Proves that you can move between list, set, and dict views.
3. **Functions and validation** — defines `accuracy`, `mean`, and `mae`, then
   calls each with invalid input and prints the rejection. Proves that failures
   are explicit.
4. **Comprehensions** — scores all runs and keeps those above 0.80. Proves that
   you can transform and filter without a loop.
5. **Dataclass** — constructs three frozen `Run` objects and prints them. Proves
   that records carry their own validation.
6. **Parsing** — converts `"3.5"`, `"n/a"`, and `""` with `parse_float`. Proves
   that untrusted text does not crash the run.
7. **Persistence** — writes and reloads `outputs/run_log.json` and
   `outputs/run_log.csv`. Proves that the record count survives the round trip.
8. **Summary** — chooses the best-accuracy and fastest run and prints a JSON
   summary. Proves that you can separate quality from cost.

Every section ends with an assertion. If an assertion fails, the notebook stops
there on purpose: a wrong intermediate result would make every later number
meaningless.

## Practical exercise

This exercise is yours to type; it is not the graded lab. Do it in a copy of the
notebook so your executed original stays intact.

1. Add a function `recall(true_positives: int, positives: int) -> float` that
   raises `ValueError` when `positives <= 0` or when `true_positives` is outside
   `[0, positives]`. Check `recall(32, 40) == 0.8` and confirm `recall(41, 40)`
   raises.
2. Add a fourth record, `{"model": "forest", "correct": 45, "total": 50,
   "latency_ms": 6.2}`, to the `records` list, and construct `Run("forest",
   accuracy(45, 50), 6.2, 5_000)`.
3. Recompute the summary. Confirm the best-accuracy model is now `forest`, the
   fastest is still `baseline`, and the mean accuracy is `0.795`.
4. Compute the accuracy gained over the baseline per extra millisecond for each
   model: `(accuracy - 0.60) / (latency_ms - 2.1)`.
5. Write a three-sentence note stating which model you would ship if a request
   must return in under 5 ms.

Expected observations:

- The gain per millisecond falls from about `0.169` for logistic, to `0.096` for
  the tree, to `0.073` for the forest. Extra accuracy gets more expensive.
- The forest wins on accuracy and loses on the 5 ms budget, so the tree or the
  logistic model is the defensible choice.
- The CSV still has one header and one row per run; after your edit it has four
  rows. If it has five, you probably wrote the header twice or appended to an
  existing file.

## Common mistakes and how to diagnose them

| Symptom | Likely cause | How to diagnose and fix |
| --- | --- | --- |
| Accuracy prints `0` or `1` | Integer division or integer inputs | Print `type(correct), type(total)`; use `/` not `//` |
| `0.1 + 0.2` comparison fails | Exact float equality | Use `math.isclose(a, b, rel_tol=1e-9)` |
| `TypeError: can only concatenate str (not "int") to str` | CSV values are strings after reload | Convert once after reading: `int(row["params"])` |
| `KeyError: 'latency'` | Misspelled key or a record built from a different schema | Print `row.keys()`; build every record from the dataclass |
| `ValueError` at construction time | An invariant rejected a real value, such as accuracy `86` instead of `0.86` | Read the message: it names the field and the valid range |
| `FileNotFoundError: outputs/run_log.json` | Working directory is not the notebook folder | `Path.cwd()` and `OUTPUT_DIR.mkdir(exist_ok=True)` |
| The script prints nothing but results are `None` | A function has no `return` | Check the last line of the function body |
| CSV has twice as many rows as expected | Opened in append mode or wrote inside a loop | Open once with `"w"` and write all rows in one call |
| Exception swallowed, values silently `None` | Bare `except:` around a conversion | Catch `(TypeError, ValueError)` and print the rejected value |

A short debugging protocol that works for every later module:

1. Reproduce the problem with the smallest possible snippet.
2. Read the last line of the traceback, then the first line that names your file.
3. Print the type and shape of the value just before the failure.
4. Change one thing, rerun, and record what happened.
5. If a result is plausible but unexpected, check the input before the algorithm.

## Checkpoint

You are ready for the lab when you can:

- [ ] State the difference between `/` and `//` without running code.
- [ ] Explain when a `dict` is a better choice than a list of tuples.
- [ ] Show that `accuracy(51, 50)` raises `ValueError` and say why that is better
      than returning `1.02`.
- [ ] Explain what `frozen=True` prevents and why a run log benefits from it.
- [ ] Read `outputs/run_log.csv` back and confirm it contains three data rows.
- [ ] Name one reason the most accurate model may not be the model you ship.

## Next step

1. Run the [guided notebook](notebook.md) from a clean kernel.
2. Complete the [lab brief](lab.md), which asks you to build a small, tested
   toolkit for a different scenario.
3. Score your evidence with the [assessment](assessment.md).
4. Continue to [M01 - Python and AI development environment](../m01-environment/index.md),
   where you will build the environment this toolkit runs in. The unit overview
   is in the [Level 0 plan](../../syllabus/level-0-start.md).

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
