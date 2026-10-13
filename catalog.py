"""Load and search the synthetic catalog without changing decimal prices."""
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    description: str
    monthly_price: Decimal


def load_catalog(path: Path) -> dict[str, Product]:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {"product_id", "name", "description", "monthly_price"}
    if not required.issubset(frame.columns):
        raise ValueError("Catalog is missing required columns.")
    products = {}
    for row in frame.to_dict("records"):
        product = Product(row["product_id"], row["name"], row["description"], Decimal(row["monthly_price"]))
        if not product.product_id or not product.name or product.product_id in products:
            raise ValueError("Catalog product IDs must be present and unique, with named products.")
        price = product.monthly_price
        if not price.is_finite() or price < 0 or price != price.quantize(Decimal("0.01")):
            raise ValueError("Catalog prices must be nonnegative USD amounts with at most two decimal places.")
        products[product.product_id] = product
    return products


def search_catalog(catalog: dict[str, Product], query: str) -> list[Product]:
    query = query.strip().casefold()
    return [product for product in catalog.values()
            if query in f"{product.product_id} {product.name} {product.description}".casefold()]
