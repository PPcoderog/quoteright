from decimal import Decimal
from pathlib import Path

from catalog import load_catalog, search_catalog

DATA = Path(__file__).resolve().parents[1] / "data" / "products.csv"


def test_catalog_preserves_exact_prices_and_searches_description():
    catalog = load_catalog(DATA)
    assert len(catalog) == 5
    assert catalog["TEAM"].monthly_price == Decimal("20.00")
    assert [p.product_id for p in search_catalog(catalog, "HANDOFFS")] == ["FLOW"]
    assert len(search_catalog(catalog, "  ")) == 5
    assert search_catalog(catalog, "nonexistent") == []
