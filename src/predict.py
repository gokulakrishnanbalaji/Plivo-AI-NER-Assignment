import json
import argparse
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from labels import ID2LABEL, label_is_pii
import os
import re


# ---------------------------------------------------------
# POST-PROCESSING HELPERS
# ---------------------------------------------------------

DIGIT_WORDS = {
    "zero", "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "oh", "o", "to", "too", "for"
}

MONTHS = {
    "january","february","march","april","may","june",
    "july","august","september","october","november","december"
}


def count_digit_like_tokens(text):
    tokens = re.split(r"[^\w]+", text.lower())
    count = 0
    for t in tokens:
        if t.isdigit():
            count += 1
        elif t in DIGIT_WORDS:
            count += 1
    return count


def is_valid_credit_card(text):
    t = text.replace(" ", "").replace("-", "")
    digit_like = count_digit_like_tokens(text)
    return (sum(c.isdigit() for c in t) >= 12) or (digit_like >= 12)


def is_valid_phone(text):
    digit_like = count_digit_like_tokens(text)
    return digit_like >= 7


def is_valid_email(text):
    lower = text.lower()
    if (" at " in lower or "@" in lower) and (
        " dot " in lower or "." in lower or "com" in lower or "org" in lower
    ):
        return True
    return False


def is_valid_person_name(text):
    if any(c.isdigit() for c in text):
        return False
    return len(text.strip()) >= 3


def is_valid_date(text):
    lower = text.lower()
    tokens = lower.split()
    has_month = any(m in tokens for m in MONTHS)
    has_year = any(
        y in lower
        for y in ["twenty", "nineteen", "two thousand", "2020", "2021", "2022"]
    )
    return has_month or has_year


def apply_postprocessing(start, end, label, text_span):
    """
    Returns (keep, label) where keep is True/False.
    """
    if label == "CREDIT_CARD":
        return is_valid_credit_card(text_span), label

    if label == "PHONE":
        return is_valid_phone(text_span), label

    if label == "EMAIL":
        return is_valid_email(text_span), label

    if label == "PERSON_NAME":
        return is_valid_person_name(text_span), label

    if label == "DATE":
        return is_valid_date(text_span), label

    # CITY, LOCATION always keep
    return True, label


# ---------------------------------------------------------
# YOUR ORIGINAL BIO → SPAN DECODER
# ---------------------------------------------------------
def bio_to_spans(text, offsets, label_ids):
    spans = []
    current_label = None
    current_start = None
    current_end = None

    for (start, end), lid in zip(offsets, label_ids):
        if start == 0 and end == 0:
            continue
        label = ID2LABEL.get(int(lid), "O")
        if label == "O":
            if current_label is not None:
                spans.append((current_start, current_end, current_label))
                current_label = None
            continue

        prefix, ent_type = label.split("-", 1)
        if prefix == "B":
            if current_label is not None:
                spans.append((current_start, current_end, current_label))
            current_label = ent_type
            current_start = start
            current_end = end
        elif prefix == "I":
            if current_label == ent_type:
                current_end = end
            else:
                if current_label is not None:
                    spans.append((current_start, current_end, current_label))
                current_label = ent_type
                current_start = start
                current_end = end

    if current_label is not None:
        spans.append((current_start, current_end, current_label))

    return spans


# ---------------------------------------------------------
# MAIN Predict Function
# ---------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", default="out")
    ap.add_argument("--model_name", default=None)
    ap.add_argument("--input", default="data/dev.jsonl")
    ap.add_argument("--output", default="out/dev_pred.json")
    ap.add_argument("--max_length", type=int, default=256)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_dir if args.model_name is None else args.model_name
    )
    model = AutoModelForTokenClassification.from_pretrained(args.model_dir)
    model.to(args.device)
    model.eval()

    results = {}

    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            text = obj["text"]
            uid = obj["id"]

            enc = tokenizer(
                text,
                return_offsets_mapping=True,
                truncation=True,
                max_length=args.max_length,
                return_tensors="pt",
            )
            offsets = enc["offset_mapping"][0].tolist()
            input_ids = enc["input_ids"].to(args.device)
            attention_mask = enc["attention_mask"].to(args.device)

            with torch.no_grad():
                out = model(input_ids=input_ids, attention_mask=attention_mask)
                logits = out.logits[0]
                pred_ids = logits.argmax(dim=-1).cpu().tolist()

            spans = bio_to_spans(text, offsets, pred_ids)
            ents = []

            for s, e, lab in spans:
                if s < 0 or e <= s or e > len(text):
                    continue

                text_span = text[s:e]

                keep, new_lab = apply_postprocessing(s, e, lab, text_span)
                if not keep:
                    continue

                ents.append({
                    "start": int(s),
                    "end": int(e),
                    "label": new_lab,
                    "pii": bool(label_is_pii(new_lab))
                })

            results[uid] = ents

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Wrote predictions for {len(results)} utterances to {args.output}")


if __name__ == "__main__":
    main()
