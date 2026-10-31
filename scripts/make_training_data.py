"""Generate the synthetic datasets used by the T01-T10 and P01-P08 units.

All data is synthetic and released CC0-1.0. No personal data, scraped text, or
third-party content is used. The generator is deterministic for a fixed seed.

Usage:
    python scripts/make_training_data.py
    python scripts/make_training_data.py --out datasets/training/generated
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 2026
LICENSE = "CC0-1.0"
GENERATOR = "scripts/make_training_data.py"

PRODUCTS = [
    "commuter bike",
    "mountain bike",
    "helmet",
    "rear light",
    "u-lock",
    "pannier bag",
    "repair stand",
    "cycling computer",
]

# ---------------------------------------------------------------------------
# Support tickets
# ---------------------------------------------------------------------------

TICKET_TEMPLATES = {
    "billing": [
        "I was charged twice for order {order} and need a refund.",
        "My invoice for order {order} shows the wrong total.",
        "The discount code did not apply to order {order}.",
        "Why was my card charged before the item shipped?",
        "I cancelled order {order} but the payment still went through.",
        "Please send a receipt for order {order} for my records.",
        "The gift card balance is wrong after order {order}.",
        "I need to update the card on file for order {order}.",
        "The monthly financing charge on order {order} looks incorrect.",
        "Can you explain the tax line on invoice {order}?",
    ],
    "technical": [
        "The app crashes when I open the route planner on order {order}.",
        "My cycling computer will not sync after the latest update.",
        "The rear light blinks twice and then turns off.",
        "The website shows an error when I try to track order {order}.",
        "Bluetooth pairing fails with the cadence sensor.",
        "The firmware update for order {order} stops at 40 percent.",
        "The route map is blank on my phone after login.",
        "The bike computer resets itself during a ride.",
        "I cannot download the ride file from order {order}.",
        "The app logs me out every time I open it.",
    ],
    "account": [
        "I cannot reset my password for the account on order {order}.",
        "Please merge my two accounts; both use the same email.",
        "I need to change the email address on my account.",
        "Two-factor authentication codes never arrive.",
        "My delivery address is outdated and I cannot edit it.",
        "The account page says my profile is incomplete.",
        "I want to delete an old saved payment method.",
        "I am locked out after too many login attempts.",
        "My order history disappeared after I changed phones.",
        "Please update the phone number on my account.",
    ],
}

RESOLUTION_NOTES = {
    "billing": "Refund approved and payment adjustment posted.",
    "technical": "Bug reproduced; app fix scheduled in the next release.",
    "account": "Password reset completed and profile corrected.",
}


def _make_tickets(rng: random.Random) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict] = []
    ticket_id = 1000
    for customer_index in range(100):
        customer_id = f"C{customer_index:03d}"
        for label in ("billing", "technical", "account"):
            for _ in range(2):
                template = rng.choice(TICKET_TEMPLATES[label])
                order = rng.randint(10000, 99999)
                text = template.format(order=order)
                rows.append(
                    {
                        "ticket_id": f"T{ticket_id}",
                        "customer_id": customer_id,
                        "created_at": f"2026-{rng.randint(1, 9):02d}-{rng.randint(1, 28):02d}",
                        "text": text,
                        "label": label,
                        "resolution_note": RESOLUTION_NOTES[label],
                    }
                )
                ticket_id += 1

    clean = pd.DataFrame(rows)
    assert len(clean) == 600
    assert clean["text"].is_unique
    assert clean.groupby("label").size().eq(200).all()

    messy_rows: list[dict] = clean.to_dict("records")

    # Exact duplicate tickets, as happen when a customer submits twice.
    duplicates = clean.sample(n=40, random_state=SEED).to_dict("records")
    for duplicate in duplicates:
        duplicate = dict(duplicate)
        duplicate["ticket_id"] = f"T{ticket_id}"
        ticket_id += 1
        messy_rows.append(duplicate)

    # Ten rows with a missing text field.
    for offset in range(10):
        template = TICKET_TEMPLATES[("billing", "technical", "account")[offset % 3]]
        messy_rows.append(
            {
                "ticket_id": f"T{ticket_id}",
                "customer_id": f"C{offset:03d}",
                "created_at": "2026-09-01",
                "text": "",
                "label": ("billing", "technical", "account")[offset % 3],
                "resolution_note": RESOLUTION_NOTES[("billing", "technical", "account")[offset % 3]],
            }
        )
        ticket_id += 1

    messy = pd.DataFrame(messy_rows).sample(frac=1.0, random_state=SEED).reset_index(drop=True)

    # Casing, whitespace, and label typos that a cleaning step must normalize.
    typo_positions = messy.sample(n=12, random_state=SEED + 1).index
    typos = {"billing": "Biling", "technical": "Tech ", "account": "acct"}
    for position in typo_positions:
        messy.at[position, "label"] = typos[messy.at[position, "label"]]
    whitespace_positions = messy.sample(n=30, random_state=SEED + 2).index
    for position in whitespace_positions:
        messy.at[position, "text"] = "  " + str(messy.at[position, "text"]) + " "

    return clean, messy


# ---------------------------------------------------------------------------
# FAQ instruction pairs
# ---------------------------------------------------------------------------

FAQ_TOPICS = {
    "returns": {
        "policy": "Unused items can be returned within 30 days with the receipt.",
        "detail": "Refunds are issued to the original payment method within 5 to 7 business days.",
        "items": ["helmet", "rear light", "pannier bag", "cycling computer"],
        "train_questions": [
            "What is the return window for a {item}?",
            "Can I return a {item} after 30 days?",
            "How do refunds work for a {item}?",
            "Do I need a receipt to return a {item}?",
            "Is return shipping free for a defective {item}?",
        ],
        "heldout_questions": [
            "How long do I have to send back a {item}?",
            "What happens if the {item} does not fit?",
            "Where does my money go after I return a {item}?",
        ],
    },
    "shipping": {
        "policy": "Orders placed before 2 pm on a business day ship the same day.",
        "detail": "Standard delivery takes 3 to 5 business days and express delivery takes 1 to 2.",
        "items": ["commuter bike", "mountain bike", "helmet", "u-lock"],
        "train_questions": [
            "When will my {item} ship?",
            "How long does standard delivery take for a {item}?",
            "Do you offer express shipping for a {item}?",
            "Will I get tracking for my {item}?",
            "Can you ship a {item} internationally?",
        ],
        "heldout_questions": [
            "If I order a {item} in the morning, does it go out today?",
            "What is the difference between standard and express for a {item}?",
            "How do I follow the delivery of my {item}?",
        ],
    },
    "warranty": {
        "policy": "Frames are covered for 5 years and components for 1 year.",
        "detail": "The warranty applies to the original owner and requires proof of purchase.",
        "items": ["commuter bike", "mountain bike", "rear light", "cycling computer"],
        "train_questions": [
            "How long is the frame warranty on a {item}?",
            "Does the warranty cover a {item} bought secondhand?",
            "What do I need to make a warranty claim for a {item}?",
            "Is crash damage covered for a {item}?",
            "How long are components covered on a {item}?",
        ],
        "heldout_questions": [
            "Will you repair a cracked frame on a {item}?",
            "Can I transfer the warranty of a {item} to a friend?",
            "What proof is required for a {item} warranty?",
        ],
    },
    "sizing": {
        "policy": "Frame size is chosen from your height using the chart on each bike page.",
        "detail": "You can test ride a bike at the shop and exchange an unused bike within 30 days.",
        "items": ["commuter bike", "mountain bike", "helmet", "cycling computer"],
        "train_questions": [
            "How do I choose the frame size for a {item}?",
            "Can I test ride a {item} before buying?",
            "What if the {item} is the wrong size?",
            "Do you exchange a {item} that does not fit?",
            "Which height range fits a medium {item}?",
        ],
        "heldout_questions": [
            "I am 175 cm tall; which {item} size should I pick?",
            "Is a fitting included when I buy a {item}?",
            "Can I swap a {item} for another size?",
        ],
    },
    "payment": {
        "policy": "We accept major credit cards, debit cards, and Northwind gift cards.",
        "detail": "Financing is available at checkout, and cards are charged when the order ships.",
        "items": ["commuter bike", "mountain bike", "helmet", "u-lock"],
        "train_questions": [
            "Which payment methods can I use for a {item}?",
            "Can I pay for a {item} with a gift card?",
            "Do you offer financing for a {item}?",
            "When is my card charged for a {item}?",
            "Can I pay cash on delivery for a {item}?",
        ],
        "heldout_questions": [
            "Is a debit card accepted for a {item}?",
            "How does the installment plan work for a {item}?",
            "Why was I charged before the {item} arrived?",
        ],
    },
    "repairs": {
        "policy": "Repair appointments are booked online or at the service desk.",
        "detail": "A standard tune-up costs 60 USD, and most repairs are ready in 2 to 3 days.",
        "items": ["commuter bike", "mountain bike", "rear light", "u-lock"],
        "train_questions": [
            "How do I book a repair for a {item}?",
            "How much is a tune-up for a {item}?",
            "How long does a repair take for a {item}?",
            "Do you provide a loaner while my {item} is repaired?",
            "Can you fix a bent {item}?",
        ],
        "heldout_questions": [
            "Is same-day service available for a {item}?",
            "What does a standard service include for a {item}?",
            "Where do I drop off a {item} for repair?",
        ],
    },
    "accessories": {
        "policy": "Accessories are compatible when the product page lists your bike model.",
        "detail": "Helmets, lights, and locks can be returned within 30 days if unused.",
        "items": ["helmet", "rear light", "u-lock", "pannier bag"],
        "train_questions": [
            "Will this {item} fit my bike?",
            "Can I return an unused {item}?",
            "How do I check compatibility for a {item}?",
            "Do you sell spare parts for a {item}?",
            "Is installation included with a {item}?",
        ],
        "heldout_questions": [
            "How can I tell whether a {item} works with my frame?",
            "What is your policy on returning an opened {item}?",
            "Do I need tools to install a {item}?",
        ],
    },
    "orders": {
        "policy": "Orders can be changed or cancelled before they ship.",
        "detail": "Order status is shown in the account page, and pickup orders are held for 7 days.",
        "items": ["commuter bike", "mountain bike", "helmet", "u-lock"],
        "train_questions": [
            "Can I cancel an order for a {item}?",
            "How do I change the address for a {item}?",
            "Where can I see the status of my {item}?",
            "What happens if a {item} is missing from my order?",
            "How long will you hold a {item} for pickup?",
        ],
        "heldout_questions": [
            "I ordered the wrong {item}; can I change it?",
            "My {item} never arrived; what should I do?",
            "Can someone else collect a {item} for me?",
        ],
    },
}


def _make_faq(rng: random.Random) -> pd.DataFrame:
    rows: list[dict] = []

    def add(topic: str, split: str, question: str) -> None:
        spec = FAQ_TOPICS[topic]
        answer = f"{spec['policy']} {spec['detail']}"
        rows.append(
            {
                "topic": topic,
                "split": split,
                "question": question.strip(),
                "answer": answer,
                "source": "Northwind Bikes synthetic FAQ (CC0-1.0)",
            }
        )

    for topic, spec in FAQ_TOPICS.items():
        items = spec["items"]
        for template_index, template in enumerate(spec["train_questions"]):
            for item in items[:3]:
                add(topic, "train", template.format(item=item))
        # Validation uses the fourth item and a subset of seen forms.
        for template in spec["train_questions"][:2]:
            add(topic, "validation", template.format(item=items[3]))
        for template in spec["heldout_questions"][:2]:
            add(topic, "test", template.format(item=items[3]))

    frame = pd.DataFrame(rows)
    key = frame["question"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True)
    assert key.is_unique, "FAQ questions must be unique across splits"
    assert set(frame["split"]) == {"train", "validation", "test"}
    return frame.sample(frac=1.0, random_state=SEED).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Sentiment reviews
# ---------------------------------------------------------------------------

POSITIVE_TEMPLATES = [
    "The {product} arrived quickly and works perfectly.",
    "I love the {product}; the quality is excellent.",
    "Setup was easy and the {product} feels sturdy.",
    "The {product} exceeded my expectations on the first ride.",
    "After a month, the {product} still performs great.",
    "I would recommend the {product} to a friend.",
    "The {product} is comfortable, reliable, and worth the price.",
    "The shop helped me choose the {product} and I am happy.",
    "I expected to dislike the {product}, but it works wonderfully.",
    "The {product} looks good, and it also performs well.",
    "Delivery was smooth and the {product} was well packed.",
    "The {product} is light, fast, and easy to use.",
]
NEGATIVE_TEMPLATES = [
    "The {product} arrived late and was damaged.",
    "I regret buying the {product}; it broke after a week.",
    "The {product} does not fit and returns are a hassle.",
    "Customer service ignored my question about the {product}.",
    "The {product} feels cheap and the brakes squeak.",
    "I would not recommend the {product} to anyone.",
    "The {product} looks nice, but it failed on the first ride.",
    "The {product} was missing parts and the instructions were useless.",
    "I expected to love the {product}, but it is disappointing.",
    "The {product} is overpriced and uncomfortable.",
    "The order was wrong and the {product} arrived scratched.",
    "The {product} stopped working after two days.",
]

SUFFIXES = [
    "",
    " I am still waiting for a reply.",
    " This was my first order from Northwind.",
    " The packaging was fine.",
    " I have photos if you need them.",
]


def _make_sentiment(rng: random.Random) -> dict[str, pd.DataFrame]:
    rows: list[dict] = []
    for label, templates in (("positive", POSITIVE_TEMPLATES), ("negative", NEGATIVE_TEMPLATES)):
        for template_index, template in enumerate(templates):
            for product in PRODUCTS:
                for suffix_index in (0, 1):
                    suffix = SUFFIXES[(template_index + suffix_index) % len(SUFFIXES)]
                    text = (template.format(product=product) + suffix).strip()
                    rows.append(
                        {
                            "text": text,
                            "label": label,
                            "template_id": f"{label}-{template_index:02d}",
                            "product": product,
                        }
                    )

    frame = pd.DataFrame(rows).drop_duplicates(subset=["text"]).reset_index(drop=True)
    assert frame["text"].is_unique
    template_ids = sorted(frame["template_id"].unique())
    rng.shuffle(template_ids)
    unseen_count = max(4, int(round(len(template_ids) * 0.15)))
    unseen_templates = set(template_ids[:unseen_count])
    remaining = [t for t in template_ids if t not in unseen_templates]
    rng.shuffle(remaining)
    val_count = max(2, int(round(len(remaining) * 0.15)))
    val_templates = set(remaining[:val_count])
    test_templates = set(remaining[val_count : 2 * val_count])
    train_templates = set(remaining[2 * val_count :])

    def subset(templates: set[str], split: str) -> pd.DataFrame:
        part = frame[frame["template_id"].isin(templates)].copy()
        part["split"] = split
        return part

    train = subset(train_templates, "train")
    validation = subset(val_templates, "validation")
    test = subset(test_templates, "test")
    test_unseen = subset(unseen_templates, "test_unseen")

    for part in (train, validation, test, test_unseen):
        assert not part.empty
        assert part["text"].is_unique
    assert train_templates.isdisjoint(val_templates | test_templates | unseen_templates)
    assert test_templates.isdisjoint(unseen_templates)

    return {
        "sentiment_train": train.sample(frac=1.0, random_state=SEED).reset_index(drop=True),
        "sentiment_validation": validation.sample(frac=1.0, random_state=SEED).reset_index(drop=True),
        "sentiment_test": test.sample(frac=1.0, random_state=SEED).reset_index(drop=True),
        "sentiment_test_unseen": test_unseen.sample(frac=1.0, random_state=SEED).reset_index(drop=True),
    }


# ---------------------------------------------------------------------------
# Tabular data
# ---------------------------------------------------------------------------


def _make_energy(rng: np.random.Generator) -> pd.DataFrame:
    n = 900
    outside_temp = rng.normal(14, 9, n).clip(-15, 38)
    house_size = rng.normal(120, 35, n).clip(40, 260)
    insulation = rng.uniform(0, 10, n)
    occupants = rng.integers(1, 6, n)
    hour = rng.integers(0, 24, n)

    base = 0.6 * house_size + 8 * occupants
    weather = np.maximum(0, 18 - outside_temp) * 2.2 + np.maximum(0, outside_temp - 22) * 1.4
    efficiency = 1.0 - 0.04 * insulation
    daily_shape = 1.0 + 0.25 * np.sin((hour - 7) / 24 * 2 * np.pi)
    target = (base + weather) * efficiency * daily_shape / 10 + rng.normal(0, 2.5, n)

    return pd.DataFrame(
        {
            "outside_temp_c": outside_temp.round(2),
            "house_size_m2": house_size.round(1),
            "insulation_score": insulation.round(2),
            "occupants": occupants,
            "hour": hour,
            "energy_kwh": target.clip(1, None).round(3),
        }
    )


def _make_sensors(rng: np.random.Generator) -> pd.DataFrame:
    n = 900
    features = rng.normal(0, 1, size=(n, 4))
    radius = np.sqrt(features[:, 0] ** 2 + features[:, 1] ** 2)
    interaction = features[:, 2] * features[:, 3]
    logit = 2.6 * (radius - 0.9) + 1.8 * interaction + rng.normal(0, 0.7, n)
    probability = 1 / (1 + np.exp(-logit))
    fault = rng.binomial(1, probability)
    frame = pd.DataFrame(features, columns=["sensor_a", "sensor_b", "sensor_c", "sensor_d"])
    frame["fault"] = fault
    return frame


# ---------------------------------------------------------------------------
# Tiny language-model corpus
# ---------------------------------------------------------------------------

CORPUS_SUBJECTS = [
    "the fox",
    "the crow",
    "the old boatman",
    "the girl",
    "the baker",
    "the black cat",
    "the traveller",
    "the gardener",
]
CORPUS_PLACES = [
    "near the river",
    "at the edge of the forest",
    "in the quiet village",
    "beside the stone bridge",
    "under the old oak",
    "on the northern road",
]
CORPUS_OBJECTS = [
    "a silver key",
    "a red scarf",
    "a small lantern",
    "a loaf of bread",
    "a broken wheel",
    "a folded map",
    "a blue stone",
]
CORPUS_VERBS = [
    "found",
    "carried",
    "hidden",
    "lost",
    "offered",
    "repaired",
    "remembered",
]
CORPUS_ENDINGS = [
    "before the rain began.",
    "and said nothing.",
    "while the wind rose.",
    "and smiled at the sky.",
    "before the sun went down.",
    "and the village grew quiet.",
]


def _make_corpus(rng: random.Random, sentences: int = 2200) -> str:
    lines: list[str] = []
    for index in range(sentences):
        subject = rng.choice(CORPUS_SUBJECTS)
        place = rng.choice(CORPUS_PLACES)
        obj = rng.choice(CORPUS_OBJECTS)
        verb = rng.choice(CORPUS_VERBS)
        ending = rng.choice(CORPUS_ENDINGS)
        sentence = f"{subject} {verb} {obj} {place} {ending}"
        lines.append(sentence.capitalize())
        if index % 6 == 5:
            lines.append("")
    return "\n".join(lines).strip() + "\n"


# ---------------------------------------------------------------------------
# Writing and manifest
# ---------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    py_rng = random.Random(SEED)
    np_rng = np.random.default_rng(SEED)

    clean, messy = _make_tickets(py_rng)
    clean.to_csv(out_dir / "tickets_clean.csv", index=False, lineterminator="\n")
    messy.to_csv(out_dir / "tickets_messy.csv", index=False, lineterminator="\n")

    _make_faq(py_rng).to_csv(out_dir / "faq_pairs.csv", index=False, lineterminator="\n")

    for name, frame in _make_sentiment(py_rng).items():
        frame.to_csv(out_dir / f"{name}.csv", index=False, lineterminator="\n")

    _make_energy(np_rng).to_csv(out_dir / "synthetic_energy.csv", index=False, lineterminator="\n")
    _make_sensors(np_rng).to_csv(out_dir / "synthetic_sensors.csv", index=False, lineterminator="\n")

    corpus = _make_corpus(py_rng)
    (out_dir / "tiny_corpus.txt").write_text(corpus, encoding="utf-8", newline="\n")

    manifest = {
        "generator": GENERATOR,
        "seed": SEED,
        "license": LICENSE,
        "description": "Synthetic teaching data for the AITopics training and fine-tuning units.",
        "files": {},
    }
    for path in sorted(out_dir.iterdir()):
        if path.name == "manifest.json":
            continue
        if path.suffix == ".csv":
            frame = pd.read_csv(path)
            manifest["files"][path.name] = {
                "sha256": _sha256(path),
                "rows": int(len(frame)),
                "columns": list(frame.columns),
            }
        else:
            text = path.read_text(encoding="utf-8")
            manifest["files"][path.name] = {
                "sha256": _sha256(path),
                "characters": len(text),
                "lines": text.count("\n"),
            }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("datasets/training/generated"),
        help="Output directory for generated CSV and text files.",
    )
    args = parser.parse_args()
    manifest = generate(args.out)
    print(f"Wrote {len(manifest['files'])} files to {args.out}")
    for name, info in manifest["files"].items():
        size = info.get("rows", info.get("characters"))
        print(f"  {name}: {size} {'rows' if 'rows' in info else 'characters'}")


if __name__ == "__main__":
    main()
