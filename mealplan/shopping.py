"""Combine the week's picks into one shopping list with merged quantities."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import asdict, dataclass

from mealplan.library import Ingredient, Library

# Each convertible unit maps to (dimension, size in base units: grams or ml).
_UNITS = {
    "g": ("mass", 1.0),
    "kg": ("mass", 1000.0),
    "oz": ("mass", 28.3495),
    "lb": ("mass", 453.592),
    "ml": ("volume", 1.0),
    "l": ("volume", 1000.0),
    "pinch": ("volume", 4.92892 / 16),
    "dash": ("volume", 4.92892 / 8),
    "tsp": ("volume", 4.92892),
    "tbsp": ("volume", 14.7868),
    "fl oz": ("volume", 29.5735),
    "cup": ("volume", 236.588),
    "pint": ("volume", 473.176),
    "quart": ("volume", 946.353),
    "gallon": ("volume", 3785.41),
}

_ALIASES = {
    "": "count", "each": "count", "ea": "count", "whole": "count",
    "gram": "g", "grams": "g", "kilogram": "kg", "kilograms": "kg",
    "ounce": "oz", "ounces": "oz", "lbs": "lb", "pound": "lb", "pounds": "lb",
    "milliliter": "ml", "milliliters": "ml", "liter": "l", "liters": "l",
    "teaspoon": "tsp", "teaspoons": "tsp", "tablespoon": "tbsp", "tablespoons": "tbsp",
    "pinches": "pinch", "dashes": "dash", "cups": "cup", "pints": "pint", "quarts": "quart", "gallons": "gallon",
    "fluid ounce": "fl oz", "fluid ounces": "fl oz",
}


def normalize_unit(unit: str) -> str:
    unit = unit.strip().lower().rstrip(".")
    unit = _ALIASES.get(unit, unit)
    # Treat simple plurals of package words alike: "cans" -> "can".
    if unit not in _UNITS and unit.endswith("s") and len(unit) > 3:
        unit = unit[:-1]
    return unit


def _display(dimension: str, base: float) -> tuple[float, str]:
    if dimension == "mass":
        return (base / 453.592, "lb") if base >= 453.592 else (base / 28.3495, "oz")
    if base >= 236.588 / 4:
        return base / 236.588, "cup"
    if base >= 14.7868:
        return base / 14.7868, "tbsp"
    if base >= 4.92892 / 4:
        return base / 4.92892, "tsp"
    return base / (4.92892 / 16), "pinch"


@dataclass
class ShoppingItem:
    item: str
    qty: float
    unit: str
    cart_qty: int  # how many to put in the cart
    category: str
    search: str
    asin: str | None
    used_in: list[str]

    def label(self) -> str:
        qty = f"{self.qty:g}" if self.qty == int(self.qty) else f"{self.qty:.2f}".rstrip("0")
        return f"{self.item} — {qty} {self.unit}"


@dataclass
class ShoppingList:
    items: list[ShoppingItem]
    pantry_check: list[ShoppingItem]

    def to_dict(self) -> dict:
        return {
            "items": [asdict(i) for i in self.items],
            "pantry_check": [asdict(i) for i in self.pantry_check],
        }


def build_shopping_list(
    library: Library,
    recipes: dict[str, float],
    snacks: dict[str, float],
    extras: list[Ingredient] | None = None,
) -> ShoppingList:
    """`recipes` and `snacks` map slug -> batches (2 means make it twice)."""
    picks = []
    for slugs, pool, kind in ((recipes, library.recipes, "recipe"), (snacks, library.snacks, "snack")):
        for slug, batches in slugs.items():
            if slug not in pool:
                raise KeyError(f"unknown {kind} '{slug}' (have: {', '.join(sorted(pool))})")
            dish = pool[slug]
            picks += [(ing, batches, dish.name) for ing in dish.ingredients]
    picks += [(ing, 1, "extra") for ing in extras or []]

    # Group by item and dimension; units that don't convert stay separate lines.
    totals: dict[tuple[str, str], float] = defaultdict(float)
    sources: dict[tuple[str, str], list[str]] = defaultdict(list)
    for ing, batches, source in picks:
        unit = normalize_unit(ing.unit)
        dimension, size = _UNITS.get(unit, (unit, 1.0))
        key = (ing.item, dimension)
        totals[key] += ing.qty * batches * size
        if source not in sources[key]:
            sources[key].append(source)

    items, pantry_check = [], []
    for (name, dimension), base in totals.items():
        if dimension in ("mass", "volume"):
            qty, unit = _display(dimension, base)
            cart_qty = 1  # buy one package; the needed amount is shown alongside
        else:
            qty, unit = base, dimension
            cart_qty = max(1, math.ceil(round(base, 6)))
        pin = library.products.get(name, {})
        entry = ShoppingItem(
            item=name,
            qty=round(qty, 2),
            unit=unit,
            cart_qty=int(pin.get("cart_qty", cart_qty)),
            category=pin.get("category", "Other"),
            search=pin.get("search", name),
            asin=pin.get("asin"),
            used_in=sources[(name, dimension)],
        )
        (pantry_check if name in library.pantry else items).append(entry)

    order = lambda i: (i.category == "Other", i.category, i.item)  # noqa: E731
    return ShoppingList(items=sorted(items, key=order), pantry_check=sorted(pantry_check, key=order))


def to_markdown(week: str, recipes: dict, snacks: dict, library: Library, shopping: ShoppingList) -> str:
    lines = [f"# Meal plan — {week}", "", "## Cooking this week"]
    for slug, n in recipes.items():
        lines.append(f"- {library.recipes[slug].name}" + (f" ×{n:g}" if n != 1 else ""))
    if snacks:
        lines += ["", "## Snacks"]
        for slug, n in snacks.items():
            lines.append(f"- {library.snacks[slug].name}" + (f" ×{n:g}" if n != 1 else ""))
    lines += ["", "## Shopping list"]
    category = None
    for item in shopping.items:
        if item.category != category:
            category = item.category
            lines += ["", f"### {category}"]
        lines.append(f"- [ ] {item.label()}  _(cart: {item.cart_qty}; for {', '.join(item.used_in)})_")
    if shopping.pantry_check:
        lines += ["", "## Check the pantry (not added to cart)"]
        lines += [f"- [ ] {i.label()}" for i in shopping.pantry_check]
    return "\n".join(lines) + "\n"
