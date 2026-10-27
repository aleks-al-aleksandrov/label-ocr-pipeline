"""Validation and parsing of OCR output from retail shelf labels.

These are clean re-implementations of the ideas used in the production pipeline,
written for this repository. They depend only on the Python standard library.
"""
from __future__ import annotations

import re

# Characters OCR engines commonly confuse with digits on printed labels.
OCR_DIGIT_FIXES = str.maketrans({"O": "0", "o": "0", "D": "0", "I": "1", "l": "1", "S": "5", "B": "8"})

PRICE_PATTERN = re.compile(r"(\d{1,4})\s*[,.]\s*(\d{2}|-)")


def fix_ocr_digits(text: str) -> str:
    """Replace letters that OCR typically reads instead of digits."""
    return text.translate(OCR_DIGIT_FIXES)


def is_valid_ean13(code: str) -> bool:
    """Check an EAN-13 code: weights 1,3,1,3... over the first 12 digits, the 13th is the check digit."""
    if len(code) != 13 or not code.isdigit():
        return False
    total = sum(int(digit) * (3 if i % 2 else 1) for i, digit in enumerate(code[:12]))
    return (10 - total % 10) % 10 == int(code[12])


def find_ean(text: str) -> str | None:
    """Return the most likely EAN-13 in OCR text, or None.

    1. Prefer a standalone 13-digit number with a valid checksum.
    2. Otherwise join digit groups that OCR split with spaces ("5 701234 567899")
       and look for a valid 13-digit window inside each group.
    Digits are never joined across other characters, so two separate numbers
    on the label cannot be glued into a false match.
    """
    fixed = fix_ocr_digits(text)
    for token in re.findall(r"(?<!\d)\d{13}(?!\d)", fixed):
        if is_valid_ean13(token):
            return token
    for group in re.findall(r"\d[\d ]*\d", fixed):
        digits = group.replace(" ", "")
        for start in range(len(digits) - 12):
            candidate = digits[start:start + 13]
            if is_valid_ean13(candidate):
                return candidate
    return None


def parse_price(text: str, low: float = 1, high: float = 5000) -> float | None:
    """Parse Danish shelf prices: '24,95' -> 24.95, '24,-' -> 24.0.

    Values outside a plausible shelf-price range are rejected, because a wrong price
    that looks valid is worse than a missing one.
    """
    match = PRICE_PATTERN.search(fix_ocr_digits(text))
    if not match:
        return None
    kroner, ore = match.groups()
    price = float(kroner) + (0 if ore == "-" else int(ore) / 100)
    return round(price, 2) if low <= price <= high else None
