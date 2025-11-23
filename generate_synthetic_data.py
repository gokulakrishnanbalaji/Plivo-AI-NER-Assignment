import json
import random
import os
import argparse
import re


# ===============================
# Light ASR-Style Noise
# ===============================

FILLERS = ["uh", "um", "hmm", "okay", "yeah", "please", "so", "actually", ""]


def maybe_misspell(word):
    if random.random() < 0.04:
        if len(word) > 4:
            i = random.randint(1, len(word)-2)
            return word[:i] + word[i+1:]
    return word


def apply_mild_noise_except_phone(text, phone_spans):
    """
    Apply mild noise but avoid modifying PHONE entity spans.
    phone_spans = list of (start, end)
    """
    protected = [0] * len(text)
    for s, e in phone_spans:
        for i in range(s, min(e, len(text))):
            protected[i] = 1

    new_chars = []
    i = 0
    while i < len(text):
        if protected[i] == 1:
            new_chars.append(text[i])
            i += 1
            continue

        # small filler insertion
        if random.random() < 0.04 and text[i] == ' ':
            new_chars.append(" " + random.choice(FILLERS) + " ")

        new_chars.append(text[i])
        i += 1

    noisy = "".join(new_chars)

    # Now apply misspell noise only outside protected spans
    words = noisy.split(" ")
    out_words = []
    idx = 0
    for w in words:
        start = idx
        end = idx + len(w)
        idx += len(w) + 1

        # check if word is inside phone span
        in_phone = False
        for ps, pe in phone_spans:
            if not (end < ps or start > pe):
                in_phone = True
                break

        if in_phone:
            out_words.append(w)
        else:
            out_words.append(maybe_misspell(w))

    return " ".join(out_words)


# ===============================
# Entity Generators
# ===============================

FIRST = ["rohan", "amit", "karthik", "vijay", "rahul", "shreya",
         "pooja", "ramesh", "anita", "divya", "megha", "suresh"]
LAST = ["mehta", "kumar", "sharma", "iyer", "reddy",
        "patel", "singh", "joshi", "yadav"]

EMAIL_DOMAINS = ["gmail dot com", "yahoo dot com", "outlook dot com"]

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]

CITIES = ["delhi", "mumbai", "chennai", "hyderabad", "pune", "bangalore", "kolkata"]
LOCATIONS = ["andheri east", "velachery", "gachibowli", "banjara hills", "salt lake"]

DIGIT_WORDS = ["zero","one","two","three","four","five","six","seven","eight","nine"]


def gen_name():
    return f"{random.choice(FIRST)} {random.choice(LAST)}"


def gen_email():
    name = gen_name().replace(" ", " dot ")
    domain = random.choice(EMAIL_DOMAINS)
    variants = [
        f"{name} at {domain}",
        f"{name} {domain}",
        f"{name} at {domain.replace(' dot ', '.')}",
    ]
    return random.choice(variants)


def gen_phone():
    digits = "".join(random.choice("0123456789") for _ in range(10))

    # Very stable, noise-free formats:
    patterns = [
        digits,
        digits[:5] + " " + digits[5:],
        "+91 " + digits,
    ]

    # Add very small spoken-digits portion (5%):
    if random.random() < 0.05:
        return " ".join(DIGIT_WORDS[int(d)] for d in digits)

    return random.choice(patterns)


def gen_credit_card():
    digits = "".join(random.choice("0123456789") for _ in range(16))
    return " ".join([digits[i:i+4] for i in range(0, 16, 4)])


def gen_date():
    day = random.randint(1, 28)
    month = random.choice(MONTHS)
    year = random.choice([2023, 2024, 2025])
    return random.choice([
        f"{day} {month} {year}",
        f"{day} {month}",
        f"{month} {day} {year}",
        f"{day} of {month} {year}",
    ])


# ===============================
# Templates (PHONE Enhanced)
# ===============================

TEMPLATES = [
    # EMAIL
    "reach me at {EMAIL}",
    "you can email me at {EMAIL}",
    "my mail id is {EMAIL}",
    "contact email is {EMAIL}",
    "please send it to {EMAIL}",
    "{EMAIL} is my email",

    # PHONE — Added richer patterns
    "call me on {PHONE}",
    "my phone number is {PHONE}",
    "reach me on {PHONE}",
    "you can call at {PHONE}",
    "my contact number is {PHONE}",
    "my number is {PHONE}",
    "mobile number is {PHONE}",
    "you can reach me at {PHONE}",
    "phone is {PHONE}",
    "contact no is {PHONE}",
    "my mobile is {PHONE}",

    # CREDIT CARD
    "my credit card number is {CREDIT_CARD}",
    "the card number is {CREDIT_CARD}",
    "please note my card is {CREDIT_CARD}",
    "card digits are {CREDIT_CARD}",

    # DATE + CITY
    "i will be in {CITY} on {DATE}",
    "i am travelling to {CITY} on {DATE}",
    "meeting is on {DATE} in {CITY}",
    "appointment scheduled on {DATE}",
    "the date is {DATE}",

    # LOCATION
    "i stay in {LOCATION}",
    "i live near {LOCATION}",
    "my address is {LOCATION}",
    "{LOCATION} is where i stay",

    # PERSON NAME
    "my name is {PERSON_NAME}",
    "{PERSON_NAME} speaking",
    "this is {PERSON_NAME}",
]


# ===============================
# Template Filler
# ===============================

def fill_template(template):
    entities = []
    text = template
    labels = re.findall(r"{(.*?)}", template)

    for label in labels:
        if label == "EMAIL": ent = gen_email()
        elif label == "PHONE": ent = gen_phone()
        elif label == "CREDIT_CARD": ent = gen_credit_card()
        elif label == "DATE": ent = gen_date()
        elif label == "CITY": ent = random.choice(CITIES)
        elif label == "LOCATION": ent = random.choice(LOCATIONS)
        elif label == "PERSON_NAME": ent = gen_name()
        else: raise ValueError(f"Unknown label {label}")

        placeholder = "{" + label + "}"
        start = text.lower().find(placeholder.lower())
        end = start + len(ent)
        entities.append({"start": start, "end": end, "label": label})
        text = text.replace(placeholder, ent, 1)

    return text, entities


# ===============================
# Utterance Builder (with PHONE protection)
# ===============================

def build_utterance(uid):
    parts = random.randint(1, 2)
    chosen = random.sample(TEMPLATES, parts)

    full_text = ""
    all_entities = []

    for tpl in chosen:
        sent, ents = fill_template(tpl)

        # Identify phone spans
        phone_spans = [(e["start"] + len(full_text), e["end"] + len(full_text))
                       for e in ents if e["label"] == "PHONE"]

        # Add to global list
        for e in ents:
            e["start"] += len(full_text)
            e["end"] += len(full_text)
            all_entities.append(e)

        # Apply noise but protect phone spans
        updated = apply_mild_noise_except_phone(sent, phone_spans)

        full_text += updated + " "

    return {
        "id": f"utt_{uid:05d}",
        "text": full_text.strip(),
        "entities": all_entities
    }


# ===============================
# Main
# ===============================

def generate(path, n):
    with open(path, "w") as f:
        for i in range(n):
            f.write(json.dumps(build_utterance(i)) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_out", default="data/train.jsonl")
    ap.add_argument("--dev_out", default="data/dev.jsonl")
    ap.add_argument("--train_size", type=int, default=1000)
    ap.add_argument("--dev_size", type=int, default=300)
    args = ap.parse_args()

    os.makedirs("data", exist_ok=True)

    print("Generating enhanced dataset...")
    generate(args.train_out, args.train_size)
    generate(args.dev_out, args.dev_size)
    print("Done.")
