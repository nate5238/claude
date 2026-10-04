"""Load the recipe library, snacks, pantry staples and product pins from YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Ingredient:
    item: str
    qty: float = 1
    unit: str = "count"


@dataclass
class Dish:
    """A recipe or a snack: anything you pick for the week."""

    slug: str
    name: str
    ingredients: list[Ingredient]
    kind: str  # "recipe" or "snack"
    servings: int | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class Library:
    recipes: dict[str, Dish]
    snacks: dict[str, Dish]
    pantry: set[str]
    products: dict[str, dict]


def _ingredients(raw: list[dict], source: str) -> list[Ingredient]:
    out = []
    for entry in raw or []:
        if "item" not in entry:
            raise ValueError(f"{source}: ingredient is missing 'item': {entry!r}")
        out.append(
            Ingredient(
                item=str(entry["item"]).strip().lower(),
                qty=float(entry.get("qty", 1)),
                unit=str(entry.get("unit", "count")).strip().lower(),
            )
        )
    return out


def _read_yaml(path: Path, default):
    if not path.exists():
        return default
    data = yaml.safe_load(path.read_text())
    return default if data is None else data


def load_library(root: Path) -> Library:
    recipes = {}
    for path in sorted((root / "recipes").glob("*.y*ml")):
        data = _read_yaml(path, {})
        recipes[path.stem] = Dish(
            slug=path.stem,
            name=data.get("name", path.stem),
            ingredients=_ingredients(data.get("ingredients"), str(path)),
            kind="recipe",
            servings=data.get("servings"),
            tags=list(data.get("tags", [])),
        )

    snacks = {
        slug: Dish(
            slug=slug,
            name=data.get("name", slug),
            ingredients=_ingredients(data.get("items"), f"snacks.yaml:{slug}"),
            kind="snack",
        )
        for slug, data in _read_yaml(root / "snacks.yaml", {}).items()
    }

    pantry = {str(p).strip().lower() for p in _read_yaml(root / "pantry.yaml", [])}
    products = {
        str(k).strip().lower(): (v or {})
        for k, v in _read_yaml(root / "products.yaml", {}).items()
    }
    return Library(recipes=recipes, snacks=snacks, pantry=pantry, products=products)
