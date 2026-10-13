from decimal import Decimal
from pathlib import Path

import pytest

from catalog import load_catalog
from pricing import calculate_quote, load_rules

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def inputs():
    return load_catalog(ROOT / "data/products.csv"), load_rules(ROOT / "data/rules.json")


def test_normal_quote_has_exact_itemized_totals_and_stays_draft(inputs):
    catalog, rules = inputs
    quote = calculate_quote(catalog, {"TEAM": 3, "FLOW": 2}, 12, "5", rules)
    assert [line.amount for line in quote.lines] == [Decimal("720.00"), Decimal("840.00")]
    assert quote.subtotal == Decimal("1560.00")
    assert quote.discount_amount == Decimal("78.00")
    assert quote.total == Decimal("1482.00")
    assert quote.status == "DRAFT"
    assert not quote.approval_required


@pytest.mark.parametrize("discount,requires_approval,total", [
    ("10", False, "18.00"), ("10.01", True, "18.00"), ("15", True, "17.00"),
    ("100", True, "0.00"),
])
def test_approval_uses_discount_input_not_rounded_amount(inputs, discount, requires_approval, total):
    catalog, rules = inputs
    quote = calculate_quote(catalog, {"TEAM": 1}, 1, discount, rules)
    assert quote.approval_required is requires_approval
    assert quote.total == Decimal(total)
    assert quote.status == "DRAFT"


def test_quantity_change_recalculates_every_total(inputs):
    catalog, rules = inputs
    before = calculate_quote(catalog, {"TEAM": 2}, 12, "15", rules)
    after = calculate_quote(catalog, {"TEAM": 3}, 12, "15", rules)
    assert (before.subtotal, before.discount_amount, before.total) == (
        Decimal("480.00"), Decimal("72.00"), Decimal("408.00"))
    assert (after.subtotal, after.discount_amount, after.total) == (
        Decimal("720.00"), Decimal("108.00"), Decimal("612.00"))


def test_discount_rounds_half_up_once_at_quote_level(inputs):
    catalog, rules = inputs
    quote = calculate_quote(catalog, {"INSIGHT": 1}, 1, "0.10", rules)
    assert quote.discount_amount == Decimal("0.02")
    assert quote.total == Decimal("14.98")


@pytest.mark.parametrize("quantities,months,discount", [
    ({}, 1, "0"), ({"UNKNOWN": 1}, 1, "0"), ({"TEAM": 0}, 1, "0"),
    ({"TEAM": -1}, 1, "0"), ({"TEAM": 1.5}, 1, "0"), ({"TEAM": True}, 1, "0"),
    ({"TEAM": 1}, 2, "0"), ({"TEAM": 1}, True, "0"),
    ({"TEAM": 1}, 1, "-1"), ({"TEAM": 1}, 1, "101"),
    ({"TEAM": 1}, 1, "NaN"), ({"TEAM": 1}, 1, "Infinity"),
    ({"TEAM": 1}, 1, "abc"), ({"TEAM": 1}, 1, "1.234"),
])
def test_invalid_inputs_fail_before_producing_a_quote(inputs, quantities, months, discount):
    catalog, rules = inputs
    with pytest.raises(ValueError):
        calculate_quote(catalog, quantities, months, discount, rules)


def test_extreme_quantity_returns_validation_error_instead_of_decimal_crash(inputs):
    catalog, rules = inputs
    with pytest.raises(ValueError, match='large|precision|range'):
        calculate_quote(catalog, {'TEAM': 10**30}, 12, '5', rules)
