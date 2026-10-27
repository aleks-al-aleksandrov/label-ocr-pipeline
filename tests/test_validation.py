import pytest

from label_ocr import find_ean, fix_ocr_digits, is_valid_ean13, parse_price


@pytest.mark.parametrize("code", ["5701234567899", "4006381333931", "0000000000000"])
def test_valid_ean13(code):
    assert is_valid_ean13(code)


@pytest.mark.parametrize("code", ["5701234567898", "570123456789", "57012345678990", "57O1234567899", ""])
def test_invalid_ean13(code):
    assert not is_valid_ean13(code)


def test_fix_ocr_digits():
    assert fix_ocr_digits("57O1 2345 S7B9") == "5701 2345 5789"


def test_find_ean_with_ocr_noise():
    assert find_ean("EAN: 57O1234567899 ») ") == "5701234567899"


def test_find_ean_skips_numbers_with_wrong_checksum():
    assert find_ean("1234567890123 5701234567899") == "5701234567899"


def test_find_ean_joins_digit_groups_split_by_ocr():
    assert find_ean("5 701234 567899") == "5701234567899"


def test_find_ean_returns_none_without_valid_code():
    assert find_ean("no barcode here 12345") is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("24,95 kr", 24.95),
        ("24.95", 24.95),
        ("24,-", 24.0),
        ("2O,5O", 20.5),
        ("Pris 1299,00", 1299.0),
    ],
)
def test_parse_price(text, expected):
    assert parse_price(text) == expected


@pytest.mark.parametrize("text", ["0,50", "9999,00", "pris", ""])
def test_parse_price_rejects_implausible_or_missing(text):
    assert parse_price(text) is None
