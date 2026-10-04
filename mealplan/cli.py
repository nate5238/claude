"""Command line: list the library, plan a week, push the list to a Whole Foods cart."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import yaml

from mealplan.library import Library, _ingredients, load_library
from mealplan.shopping import build_shopping_list, to_markdown

ROOT = Path(__file__).resolve().parent.parent


def _current_week() -> str:
    year, week, _ = dt.date.today().isocalendar()
    return f"{year}-W{week:02d}"


def _parse_picks(values: list[str]) -> dict[str, float]:
    """`["tacos", "oats:2"]` -> {"tacos": 1, "oats": 2}."""
    picks: dict[str, float] = {}
    for value in values or []:
        slug, _, batches = value.partition(":")
        picks[slug] = picks.get(slug, 0) + float(batches or 1)
    return picks


def _ask(prompt: str, options: dict) -> dict[str, float]:
    slugs = list(options)
    for n, slug in enumerate(slugs, 1):
        print(f"  {n:>2}. {options[slug].name}  [{slug}]")
    raw = input(f"{prompt} (numbers or slugs, e.g. '1 3:2'; blank for none): ").split()
    chosen = []
    for token in raw:
        key, _, batches = token.partition(":")
        slug = slugs[int(key) - 1] if key.isdigit() else key
        chosen.append(f"{slug}:{batches}" if batches else slug)
    return _parse_picks(chosen)


def cmd_list(library: Library, _args) -> int:
    print("Recipes:")
    for slug, dish in library.recipes.items():
        tags = f"  ({', '.join(dish.tags)})" if dish.tags else ""
        print(f"  {slug:<24} {dish.name}{tags}")
    print("Snacks:")
    for slug, dish in library.snacks.items():
        print(f"  {slug:<24} {dish.name}")
    return 0


def cmd_plan(library: Library, args) -> int:
    recipes, snacks = _parse_picks(args.recipe), _parse_picks(args.snack)
    if not recipes and not snacks:
        print("Recipes:")
        recipes = _ask("Which recipes this week?", library.recipes)
        print("Snacks:")
        snacks = _ask("Which snacks?", library.snacks)
    extras = _ingredients([{"item": e} for e in args.extra], "--extra")

    shopping = build_shopping_list(library, recipes, snacks, extras)
    out_dir = ROOT / "plans"
    out_dir.mkdir(exist_ok=True)
    plan = {
        "week": args.week,
        "recipes": recipes,
        "snacks": snacks,
        "extras": [e.item for e in extras],
    }
    (out_dir / f"{args.week}.yaml").write_text(yaml.safe_dump(plan, sort_keys=False))
    (out_dir / f"{args.week}-shopping.json").write_text(
        json.dumps({"week": args.week, **shopping.to_dict()}, indent=2)
    )
    md = to_markdown(args.week, recipes, snacks, library, shopping)
    (out_dir / f"{args.week}-shopping.md").write_text(md)
    print(md)
    print(f"Saved plans/{args.week}-shopping.md and .json")
    return 0


def cmd_cart(_library: Library, args) -> int:
    from mealplan.cart import fill_cart  # Playwright is only needed for this step

    path = Path(args.list or ROOT / "plans" / f"{args.week}-shopping.json")
    return fill_cart(json.loads(path.read_text())["items"], confirm_each=args.confirm_each)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mealplan", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="show recipes and snacks").set_defaults(func=cmd_list)

    plan = sub.add_parser("plan", help="pick this week's recipes/snacks and build the shopping list")
    plan.add_argument("--week", default=_current_week(), help="e.g. 2026-W40 (default: this week)")
    plan.add_argument("--recipe", "-r", action="append", default=[], help="slug or slug:batches; repeatable")
    plan.add_argument("--snack", "-s", action="append", default=[], help="slug or slug:count; repeatable")
    plan.add_argument("--extra", "-e", action="append", default=[], help="one-off item, e.g. 'coffee beans'")
    plan.set_defaults(func=cmd_plan)

    cart = sub.add_parser("cart", help="add a shopping list to your Whole Foods cart on Amazon")
    cart.add_argument("--week", default=_current_week())
    cart.add_argument("--list", help="path to a *-shopping.json (default: this week's)")
    cart.add_argument("--confirm-each", action="store_true", help="pause so you can pick each product yourself")
    cart.set_defaults(func=cmd_cart)

    args = parser.parse_args(argv)
    return args.func(load_library(ROOT), args)
