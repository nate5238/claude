# Meal planner → Whole Foods cart

Keep your recipes here, pick what you're cooking each week, and get one merged shopping
list that Claude (or a script) adds to your Whole Foods cart on Amazon.

## Your library

- **`recipes/`** — one YAML file per recipe:
  ```yaml
  name: Chicken Tacos
  servings: 4
  tags: [dinner]
  ingredients:
    - {item: boneless skinless chicken thighs, qty: 1.5, unit: lb}
    - {item: limes, qty: 2, unit: count}
  ```
- **`snacks.yaml`** — snacks, each a list of items to buy.
- **`pantry.yaml`** — staples you keep stocked; they go on a "check the pantry" list instead of the cart.
- **`products.yaml`** — optional: pin an ingredient to a search phrase or exact product (`asin`),
  a store section (`category`), or a cart quantity (`cart_qty`).

The three recipes and snacks included are examples — replace them with yours, or paste a recipe
to Claude and ask it to add it.

## Each week

**With Claude Code** (in this repo): say "plan my meals" or run `/meal-plan`. Claude lists your
recipes, asks what you want, builds the list, and — if it has browser access (Claude in Chrome) —
adds everything to your Whole Foods cart. It never checks out; you review the cart and pick a
delivery time.

**By hand:**
```sh
pip install -r requirements.txt
python -m mealplan list
python -m mealplan plan                      # interactive, or:
python -m mealplan plan -r chicken-tacos -r overnight-oats:2 -s trail-mix -e "coffee beans"
python -m mealplan cart                      # opens a browser; sign in to Amazon once
```

`plan` merges quantities across recipes (2 tbsp + 1/4 cup olive oil → one line), multiplies
batches, and writes `plans/<week>.yaml` plus `plans/<week>-shopping.md` / `.json`.

`cart` uses Playwright with its own browser profile in `~/.mealplan/`. It runs on your computer
(not in a cloud session, since it needs your Amazon login). Amazon changes its pages often, so
when it can't find an "Add to cart" button it pauses for you to add the item, and `--confirm-each`
lets you choose every product yourself. At the end it prints product IDs you can paste into
`products.yaml` so the same items get picked next time.

## Tests

```sh
python -m unittest discover -s tests
```
