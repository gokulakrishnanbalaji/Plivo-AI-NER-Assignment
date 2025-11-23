import json
import random
import os
import argparse
import re


# ===============================
# Light, realistic ASR-style noise
# ===============================

FILLERS = ["uh", "um", "hmm", "okay", "yeah", "please", "so", "actually", ""]


def maybe_misspell(word):
    """Tiny, realistic misspellings."""
    if random.random() < 0.04:
        if len(word) > 4:
            i = random.randint(1, len(word)-2)
            return word[:i] + word[i+1:]  # delete one character
    return word


def apply_mild_noise(text):
    """Add light, realistic noise without destroying meaning."""
    words = text.split()
    out = []

    for w in words:
        # small filler insertion
        if random.random() < 0.04:
            out.append(random.choice(FILLERS))

        # tiny misspell
        out.append(maybe_misspell(w))

    return " ".join([w for w in out if w])


# ===============================
# Entity generators
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
    # 80% numeric, 20% spoken
    if random.random() < 0.2:
        return " ".join(DIGIT_WORDS[int(d)] for d in digits)
    return digits


def gen_credit_card():
    digits = "".join(random.choice("0123456789") for _ in range(16))
    blocks = [digits[i:i+4] for i in range(0, 16, 4)]

    # 75% clean numeric format, 25% spoken
    if random.random() < 0.25:
        return " ".join(DIGIT_WORDS[int(d)] for d in digits)
    return " ".join(blocks)


def gen_date():
    day = random.randint(1, 28)
    month = random.choice(MONTHS)
    year = random.choice([2023, 2024, 2025])
    formats = [
        f"{day} {month} {year}",
        f"{day} {month}",
        f"{month} {day} {year}",
        f"{day} of {month} {year}",
    ]
    return random.choice(formats)


# ===============================
# Natural, realistic templates
# ===============================

TEMPLATES = [
    # EMAIL
    "reach me at {EMAIL}",
    "you can email me at {EMAIL}",
    "my mail id is {EMAIL}",
    "contact email is {EMAIL}",
    "please send it to {EMAIL}",
    "{EMAIL} is my email",

    # PHONE
    "call me on {PHONE}",
    "my phone number is {PHONE}",
    "reach me on {PHONE}",
    "you can call at {PHONE}",
    "my contact number is {PHONE}",

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
# Fill all placeholders correctly
# ===============================

def fill_template(template):
    """
    Replaces ALL placeholders ({EMAIL}, {PHONE}, etc.)
    and returns (text, list_of_entity_spans)
    """
    entities = []
    text = template

    labels = re.findall(r"{(.*?)}", template)

    for label in labels:
        if label == "EMAIL":
            ent = gen_email()
        elif label == "PHONE":
            ent = gen_phone()
        elif label == "CREDIT_CARD":
            ent = gen_credit_card()
        elif label == "DATE":
            ent = gen_date()
        elif label == "CITY":
            ent = random.choice(CITIES)
        elif label == "LOCATION":
            ent = random.choice(LOCATIONS)
        elif label == "PERSON_NAME":
            ent = gen_name()
        else:
            raise ValueError(f"Unknown label {label}")

        # find placeholder location
        placeholder = "{" + label + "}"
        start = text.lower().find(placeholder.lower())
        end = start + len(ent)

        entities.append({"start": start, "end": end, "label": label})

        # replace FIRST occurrence ONLY
        text = text.replace(placeholder, ent, 1)

    return text, entities


# ===============================
# Utterance builder
# ===============================

def build_utterance(uid):
    parts = random.randint(1, 2)
    chosen = random.sample(TEMPLATES, parts)

    full_text = ""
    all_entities = []

    for tpl in chosen:
        sentence, ents = fill_template(tpl)
        sentence = apply_mild_noise(sentence)

        # adjust entity spans
        for e in ents:
            e["start"] += len(full_text)
            e["end"] += len(full_text)
            all_entities.append(e)

        full_text += sentence + " "

    return {
        "id": f"utt_{uid:05d}",
        "text": full_text.strip(),
        "entities": all_entities,
    }


# ===============================
# Main generation function
# ===============================

def generate(path, n):
    with open(path, "w") as f:
        for i in range(n):
            f.write(json.dumps(build_utterance(i)) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_out", default="data/train.jsonl")
    ap.add_argument("--dev_out", default="data/dev.jsonl")
    ap.add_argument("--train_size", type=int, default=2000)
    ap.add_argument("--dev_size", type=int, default=300)
    args = ap.parse_args()

    os.makedirs("data", exist_ok=True)

    print("Generating realistic training data...")
    generate(args.train_out, args.train_size)

    print("Generating realistic dev data...")
    generate(args.dev_out, args.dev_size)

    print("Done. Realistic dataset generated successfully.")
