"""Generate the capstone starter datasets for P02 (text classification) and P03 (LoRA).

Run once, from the repository root:

    python scripts/make_capstone_data.py
    python scripts/make_capstone_data.py --check

Outputs, all under ``data/capstones/`` (git-ignored because generated):

    tickets/train.csv|val.csv|test.csv   labelled support tickets, 5 intents
    tickets/leakage.json                 template overlap between splits (must be 0)
    tickets/dataset_card.md              provenance, licence, known issues
    instructions/train.jsonl|val.jsonl|test.jsonl
                                         instruction/response pairs for LoRA
    manifest.json                        sha256 + size for every generated file

Design notes that matter for the projects:

* Splits are grouped by **template id**, so a student cannot score well by
  memorising one sentence pattern. ``leakage.json`` proves the overlap is zero.
* Every ticket carries a shared courtesy sentence that appears in all five
  classes. A bag-of-words model that latches onto politeness gains nothing.
* The instruction pairs are template-generated, not human-written. They teach the
  mechanics of a fine-tuning pipeline; they are not a quality benchmark, and the
  dataset card says so.

Everything is synthetic, deterministic at the documented seed, and released with
the course under CC0-1.0. No personal data, no scraped text.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

SEED = 20261104
OUT = Path("data") / "capstones"

INTENTS = ["billing", "delivery", "refund", "account", "technical"]

PRODUCTS = ["the starter plan", "the annual plan", "the team plan", "the mobile app",
            "the desktop app", "the sync add-on", "the backup add-on"]

COURTESY = [
    "I have been a customer for a while and I usually like the service.",
    "Sorry to bother you, I know you are busy.",
    "Thanks in advance for looking into this.",
    "I have written in before about something similar.",
]

TEMPLATES: dict[str, list[str]] = {
    "billing": [
        "I was charged twice for {product} this month and I need the duplicate payment reversed.",
        "My invoice for {product} shows an amount I did not agree to. Please explain the line item.",
        "The price of {product} went up without any notice on my statement.",
        "I cancelled {product} but the subscription is still billing me every month.",
        "Why does my receipt for {product} include a tax line that was not there last year?",
        "My card was declined for {product} even though the balance is fine. Is the charge still pending?",
        "I need a proper VAT invoice for {product}; the download link gives me a receipt only.",
        "The discount code for {product} was accepted at checkout but never applied to the charge.",
    ],
    "delivery": [
        "My order of {product} was meant to arrive on day {days} and the tracking has not moved.",
        "The parcel for {product} was left at the wrong address and nobody can find it.",
        "I paid for next-day delivery of {product} and it arrived {days} days late.",
        "The delivery driver marked {product} as handed to me, but I never received it.",
        "My shipment of {product} arrived damaged because the box was crushed in transit.",
        "Can you change the delivery address for {product}? It has not shipped yet.",
        "Only part of my order arrived; the rest of {product} is missing from the box.",
        "The courier keeps rescheduling delivery of {product} without telling me why.",
    ],
    "refund": [
        "I returned {product} {days} days ago and the refund has not appeared on my statement.",
        "You promised a refund for {product} but only part of the amount came back.",
        "I was told {product} was non-refundable after I had already paid for it.",
        "Please refund {product}; it does not do what the product page says it does.",
        "The refund for {product} went to an old card that no longer exists.",
        "I cancelled within the cooling-off period and still have no refund for {product}.",
        "I want a refund for {product} because I was charged for a renewal I did not request.",
        "How long should a refund for {product} take? It has been {days} days.",
    ],
    "account": [
        "I cannot sign in to my account; the password reset email never arrives.",
        "Someone changed the email address on my account and I am locked out.",
        "I need to merge two accounts that were created with different addresses.",
        "Please delete my account and all stored data, as I am leaving the service.",
        "Two-factor authentication is asking for a code from a phone I no longer have.",
        "My profile keeps reverting the display name after I save it.",
        "I want to add a colleague to the account, but the invite link expires immediately.",
        "The account page shows a plan I never selected and will not let me change it.",
    ],
    "technical": [
        "The app crashes on launch after the latest update on my phone.",
        "Sync stops after a few minutes and I have to restart {product} to get it working.",
        "Uploads fail with an error code and no explanation when the file is large.",
        "The export produces an empty file every time I try it from {product}.",
        "Search returns nothing even for words I can see in my own documents.",
        "The desktop client uses all my memory after a few hours and the machine freezes.",
        "Notifications arrive hours late, so I miss messages during the working day.",
        "The integration with our calendar disconnects every morning without warning.",
    ],
}

REPLIES = {
    "billing": ("I have checked the charge for {product}. A duplicate authorisation can sit on a card for "
                "up to five working days. I have cancelled the second charge and sent a corrected invoice "
                "to your billing email. If it still appears after five working days, reply to this message "
                "and we will escalate it with the payment provider."),
    "delivery": ("I am sorry the delivery of {product} did not arrive as expected. I have opened a trace "
                 "with the courier; they respond within two working days. If the parcel is confirmed lost, "
                 "we will send a replacement at no cost or refund the shipping fee, whichever you prefer."),
    "refund": ("Your return for {product} has been logged. Refunds are issued to the original payment "
               "method and usually appear within five to ten working days after the return is scanned. "
               "I have marked the case for priority review and will confirm by email once the refund is "
               "released."),
    "account": ("I can help with access to your account. For security, I will send a verification link to "
                "the address on file rather than changing details from this message. Once you confirm the "
                "link, I can restore access or complete the deletion request you asked about."),
    "technical": ("Thank you for the report about {product}. Please send the app version, your operating "
                  "system, and the exact error text. In the meantime, signing out and back in clears the "
                  "local cache for most sync and upload failures; if that does not help, we will collect "
                  "logs from the client."),
}

SUBJECTS = {
    "billing": ["Duplicate charge", "Invoice question", "Unexpected price change", "Billing after cancellation"],
    "delivery": ["Late delivery", "Parcel not received", "Damaged shipment", "Wrong address"],
    "refund": ["Refund not received", "Partial refund", "Refund to old card", "Renewal refund"],
    "account": ["Cannot sign in", "Account locked", "Delete my data", "Invite link problem"],
    "technical": ["App crashes", "Sync stops", "Upload error", "Export is empty"],
}


def ticket_rows(rng: random.Random) -> list[dict]:
    rows: list[dict] = []
    index = 0
    for intent in INTENTS:
        for template_id, template in enumerate(TEMPLATES[intent]):
            for variant in range(12):
                # Keep the product on the row: the reply must refer to the product
                # the customer actually named, not a fresh random choice.
                product = rng.choice(PRODUCTS)
                text = template.format(product=product, days=rng.choice([2, 3, 5, 7, 10, 14]))
                courtesy = rng.choice(COURTESY)
                # Courtesy is shared across classes on purpose: it is not a signal.
                body = f"{courtesy} {text}"
                if variant % 4 == 3:
                    body = body.replace("I ", "I really ", 1)
                rows.append(
                    {
                        "id": f"t{index:04d}",
                        "text": body,
                        "label": intent,
                        "template_id": f"{intent}-{template_id}",
                        "product": product,
                        "subject": rng.choice(SUBJECTS[intent]),
                    }
                )
                index += 1
    rng.shuffle(rows)
    return rows


def grouped_split(rows: list[dict], fractions=(0.7, 0.15, 0.15)) -> dict[str, list[dict]]:
    """Split by template id, stratified by label, so no pattern crosses splits.

    Sorting all templates and slicing once would put every template of the
    alphabetically last label into the test split; each label is split separately.
    """
    by_template: dict[str, list[dict]] = {}
    for row in rows:
        by_template.setdefault(row["template_id"], []).append(row)

    by_label: dict[str, list[str]] = {}
    for key, group in by_template.items():
        by_label.setdefault(group[0]["label"], []).append(key)

    rng = random.Random(SEED)
    assignment: dict[str, str] = {}
    for label in sorted(by_label):
        keys = sorted(by_label[label])
        rng.shuffle(keys)
        n_train = max(1, int(len(keys) * fractions[0]))
        n_val = max(1, int(len(keys) * fractions[1])) if len(keys) >= 4 else 0
        n_val = 0 if len(keys) < 4 else n_val
        for position, key in enumerate(keys):
            if position < n_train:
                assignment[key] = "train"
            elif position < n_train + n_val:
                assignment[key] = "val"
            else:
                assignment[key] = "test"

    out: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for key, group in by_template.items():
        out[assignment[key]].extend(group)

    sets = {name: {row["template_id"] for row in group} for name, group in out.items()}
    overlap = (sets["train"] & sets["test"]) | (sets["val"] & sets["test"])
    assert not overlap, f"template leakage: {overlap}"
    assert all(out[name] for name in ("train", "val", "test")), "empty split"
    return out


def instruction_rows(rng: random.Random, rows: list[dict]) -> list[dict]:
    # ``rng`` is kept in the signature for callers from the original generator;
    # the reply now uses the product on the ticket, so no draw happens here.
    out = []
    for row in rows:
        reply = REPLIES[row["label"]].format(product=row["product"])
        out.append(
            {
                "id": f"i{len(out):04d}",
                "instruction": "Draft a first reply to this support ticket. Be specific, do not promise "
                               "anything you cannot verify, and do not ask for a password.",
                "input": row["text"],
                "output": reply,
                "label": row["label"],
                "template_id": row["template_id"],
                "product": row["product"],
            }
        )
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def build(out: Path = OUT) -> dict:
    rng = random.Random(SEED)
    rows = ticket_rows(rng)
    splits = grouped_split(rows)
    for name, group in splits.items():
        write_csv(out / "tickets" / f"{name}.csv", group)
    (out / "tickets" / "leakage.json").write_text(
        json.dumps(
            {
                "grouping": "template_id",
                "splits": {name: {"rows": len(group), "templates": len({r['template_id'] for r in group})}
                           for name, group in splits.items()},
                "template_overlap": 0,
                "label_counts": {name: {intent: sum(1 for r in group if r["label"] == intent)
                                       for intent in INTENTS} for name, group in splits.items()},
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    pairs = instruction_rows(rng, rows)
    pair_splits = grouped_split(pairs)
    for name, group in pair_splits.items():
        write_jsonl(out / "instructions" / f"{name}.jsonl", group)

    # A small standalone generation set drawn from held-out templates. Keeping
    # prompts, references, and template ids together lets a student evaluate
    # free-running generation without reusing the training split.
    generation_rows = [
        {
            "id": row["id"],
            "instruction": row["instruction"],
            "input": row["input"],
            "reference": row["output"],
            "label": row["label"],
            "template_id": row["template_id"],
            "product": row["product"],
            "source_split": "test",
        }
        for row in pair_splits["test"][::3]
    ]
    write_jsonl(out / "instructions" / "generation_eval.jsonl", generation_rows)

    (out / "tickets" / "dataset_card.md").write_text(
        "\n".join(
            [
                "# Capstone ticket dataset",
                "",
                f"- **Source:** generated by `scripts/make_capstone_data.py`, seed {SEED}.",
                "- **Licence:** CC0-1.0 with the course. No third-party text.",
                "- **Size:** 480 rows, 5 intents, 40 templates x 12 variants.",
                "- **Generation evaluation:** `instructions/generation_eval.jsonl` has 40 held-out prompts",
                "  drawn from test templates; references are for scoring only, never training.",
                "- **Splits:** grouped by `template_id`; `leakage.json` records zero overlap.",
                "- **Personal data:** none. Addresses, names, and card numbers are absent.",
                "- **Known issues:**",
                "  - Template-generated language is repetitive. A model can learn phrasing,",
                "    not intent; the grouped split limits the damage but does not remove it.",
                "  - One courtesy sentence appears in every class, so politeness is a distractor.",
                "  - No real customer wrote these tickets. Accuracy here does not predict accuracy",
                "    on real support traffic.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    manifest = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            manifest[str(path.relative_to(out)).replace("\\", "/")] = {
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def check(out: Path = OUT) -> int:
    manifest_path = out / "manifest.json"
    if not manifest_path.exists():
        print(f"missing {manifest_path}; run scripts/make_capstone_data.py")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    problems = []
    for name, entry in manifest.items():
        path = out / name
        if not path.exists():
            problems.append(f"missing {name}")
        elif sha256(path) != entry["sha256"]:
            problems.append(f"changed {name}")
    if problems:
        print("manifest mismatch:\n  " + "\n  ".join(problems))
        return 1
    print(f"ok: {len(manifest)} files match the manifest")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true", help="verify checksums only")
    args = parser.parse_args()
    if args.check:
        return check(args.out)
    manifest = build(args.out)
    total = sum(entry["bytes"] for entry in manifest.values())
    print(f"wrote {len(manifest)} files, {total:,} bytes to {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
