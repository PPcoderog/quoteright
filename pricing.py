"""Authoritative, deterministic quoting. No UI or model dependencies."""
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path

from catalog import Product

CENT = Decimal("0.01")


@dataclass(frozen=True)
class Rules:
    currency: str
    allowed_months: tuple[int, ...]
    approval_threshold_percent: Decimal


@dataclass(frozen=True)
class QuoteLine:
    product: Product
    quantity: int
    months: int
    amount: Decimal


@dataclass(frozen=True)
class Quote:
    lines: tuple[QuoteLine, ...]
    subtotal: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    total: Decimal
    approval_required: bool
    currency: str
    status: str = "DRAFT"


def load_rules(path: Path) -> Rules:
    raw = json.loads(path.read_text())
    threshold = Decimal(raw["approval_threshold_percent"])
    terms = tuple(raw["allowed_months"])
    if raw["currency"] != "USD" or not terms or any(type(m) is not int or m <= 0 for m in terms):
        raise ValueError("Rules must specify USD and positive integer terms.")
    if not threshold.is_finite() or not 0 <= threshold <= 100:
        raise ValueError("Approval threshold must be between 0 and 100.")
    return Rules(raw["currency"], terms, threshold)


def calculate_quote(
    catalog: dict[str, Product], quantities: dict[str, int], months: int,
    discount_percent: str, rules: Rules,
) -> Quote:
    with localcontext() as context:
        context.prec = 64
        return _calculate_quote(catalog, quantities, months, discount_percent, rules)


def _calculate_quote(catalog, quantities, months, discount_percent, rules) -> Quote:
    if not quantities:
        raise ValueError("Select at least one product to calculate a draft.")
    if type(months) is not int or months not in rules.allowed_months:
        raise ValueError("Choose an allowed quote duration.")
    try:
        discount = Decimal(str(discount_percent))
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid discount percentage.") from None
    if not discount.is_finite() or not 0 <= discount <= 100:
        raise ValueError("Discount must be between 0 and 100%.")
    if discount != discount.quantize(CENT):
        raise ValueError("Discount must have at most two decimal places.")
    lines = []
    for product_id, quantity in quantities.items():
        if product_id not in catalog:
            raise ValueError("Select products from the catalog.")
        if type(quantity) is not int or quantity <= 0:
            raise ValueError("Each quantity must be a positive whole number.")
        if quantity > 10**18:
            raise ValueError("The quantity is too large for the prototype's supported numeric range.")
        product = catalog[product_id]
        lines.append(QuoteLine(product, quantity, months, product.monthly_price * quantity * months))
    subtotal = sum((line.amount for line in lines), Decimal("0.00"))
    discount_amount = (subtotal * discount / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    return Quote(tuple(lines), subtotal, discount, discount_amount, subtotal - discount_amount,
                 discount > rules.approval_threshold_percent, rules.currency)
