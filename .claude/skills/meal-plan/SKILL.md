---
name: meal-plan
description: Weekly meal planning. Use when the user wants to plan this week's meals or snacks, add or edit a recipe, build a shopping list, or fill their Whole Foods (Amazon) cart. Triggers on "meal plan", "plan my week", "what should I cook", "shopping list", "Whole Foods cart", or /meal-plan.
---

# Weekly meal plan → Whole Foods cart

The repo holds the user's recipe library and a small Python tool (`python -m mealplan`).

| File | What it holds |
|---|---|
| `recipes/<slug>.yaml` | One recipe: `name`, `servings`, `tags`, `ingredients: [{item, qty, unit}]` |
| `snacks.yaml` | Snacks: `slug: {name, items: [{item, qty, unit}]}` |
| `pantry.yaml` | Staples kept on hand: left off the cart, listed under "Check the pantry" |
| `products.yaml` | Per-ingredient pins: `search`, `asin`, `category`, `cart_qty` |
| `plans/<week>.yaml`, `plans/<week>-shopping.{md,json}` | Output of each week's plan |

## 1. Pick the week's menu

1. Run `python -m mealplan list` and show the user the recipes and snacks.
2. Ask (use AskUserQuestion with multiSelect when it fits) which recipes and snacks they
   want this week, how many batches of each, and any one-off extras (coffee, paper towels…).
   If they recently planned a week, mention what they had (`plans/`) so they can vary it.
3. Run `python -m mealplan plan -r <slug>[:batches] ... -s <slug>[:count] ... -e "<extra>" ...`
   and show the resulting `plans/<week>-shopping.md`.
4. Ask whether anything in "Check the pantry" is running low; add those as `-e` extras and re-run.

## 2. Add a recipe

When the user pastes a recipe or a link, write `recipes/<kebab-slug>.yaml` in the format above.
Use lowercase, store-style ingredient names that match existing ones (reuse `limes`, not `lime`)
so quantities merge. Use units `lb`, `oz`, `cup`, `tbsp`, `tsp`, `count`, or a package word
(`bunch`, `head`, `can`, `jar`). Add any new staples to `pantry.yaml` only if the user says so.

## 3. Fill the Whole Foods cart

Never check out or pick a delivery window — the user reviews the cart and does that.

**If browser tools are available (Claude in Chrome / computer use)**, drive the user's own
signed-in browser from `plans/<week>-shopping.json`:
- Start at `https://www.amazon.com/alm/storefront?almBrandId=VUZHIFdob2xlIEZvb2Rz`; confirm the
  user is signed in and Whole Foods delivery is set up for their address.
- For each item in `items`: with an `asin`, open
  `https://www.amazon.com/dp/<asin>?almBrandId=VUZHIFdob2xlIEZvb2Rz&fpw=alm`; otherwise search
  `https://www.amazon.com/s?k=<search>&i=wholefoods` and choose the result that best matches the
  item and the needed amount (prefer a size that covers `qty unit`, organic/365 brand only if
  the user prefers it). Add `cart_qty` of it.
- Skip `pantry_check` items. Ask the user when a choice is unclear or an item is unavailable.
- Finish with a summary: what was added, substitutions, anything skipped. Offer to save the
  chosen products' ASINs to `products.yaml` so next week picks the same ones.

**Otherwise**, tell the user to run this on their own computer (it opens a browser they sign
in to once): `pip install -r requirements.txt && playwright install chromium && python -m mealplan cart`
(add `--confirm-each` to choose every product themselves).
