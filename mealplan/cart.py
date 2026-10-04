"""Add a shopping list to the Whole Foods cart on amazon.com with Playwright.

Run this on your own computer: it opens a visible Chrome window using a
dedicated profile, so you sign in to Amazon once and stay signed in. Nothing
is checked out; you review the cart and pick a delivery window yourself.

Amazon's page layout changes often. When an item can't be added automatically
the script pauses so you can add it by hand, then moves on.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

WHOLE_FOODS = "VUZHIFdob2xlIEZvb2Rz"  # Amazon's almBrandId for Whole Foods Market
PROFILE_DIR = Path.home() / ".mealplan" / "browser-profile"

ADD_BUTTONS = [
    "#freshAddToCartButton input",
    "#freshAddToCartButton button",
    "#add-to-cart-button",
    "input[name='submit.addToCart']",
    "button:has-text('Add to cart')",
    "button:has-text('Add to Cart')",
]


def _search_url(query: str) -> str:
    return f"https://www.amazon.com/s?k={quote_plus(query)}&i=wholefoods"


def _product_url(asin: str) -> str:
    return f"https://www.amazon.com/dp/{asin}?almBrandId={WHOLE_FOODS}&fpw=alm"


def _click_add(page) -> bool:
    for selector in ADD_BUTTONS:
        button = page.locator(selector).first
        if button.count() and button.is_visible():
            button.click()
            page.wait_for_timeout(1500)
            return True
    return False


def _set_quantity(page, qty: int) -> None:
    """Bump the quantity stepper that replaces the add button after the first add."""
    for _ in range(qty - 1):
        plus = page.locator("[aria-label*='Increase quantity'], button:has-text('+')").first
        if not plus.count():
            return
        plus.click()
        page.wait_for_timeout(700)


def fill_cart(items: list[dict], confirm_each: bool = False) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright isn't installed. Run: pip install playwright && playwright install chromium")
        return 1

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    manual, picked = [], {}
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(str(PROFILE_DIR), headless=False)
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto(f"https://www.amazon.com/alm/storefront?almBrandId={WHOLE_FOODS}")
        input("Sign in to Amazon and set your delivery address in the browser window, then press Enter... ")

        for item in items:
            label = f"{item['item']} (need {item['qty']:g} {item['unit']}, cart qty {item['cart_qty']})"
            print(f"→ {label}")
            if item.get("asin"):
                page.goto(_product_url(item["asin"]))
            else:
                page.goto(_search_url(item["search"]))
                first = page.locator("[data-component-type='s-search-result'] h2 a").first
                if first.count():
                    picked[item["item"]] = page.locator(
                        "[data-component-type='s-search-result']"
                    ).first.get_attribute("data-asin")
                    first.click()
                    page.wait_for_load_state("domcontentloaded")

            if confirm_each:
                input("  Adjust the product if needed, add it, then press Enter... ")
                continue
            if _click_add(page):
                _set_quantity(page, item["cart_qty"])
                print("  added")
            else:
                manual.append(label)
                input("  Couldn't find the add button. Add it by hand, then press Enter... ")

        page.goto("https://www.amazon.com/cart")
        print("\nDone. Review the Whole Foods cart in the browser and choose a delivery window.")
        if manual:
            print("Added by hand:\n  " + "\n  ".join(manual))
        if picked:
            print("\nTo get the same products next week, add these to products.yaml:")
            for name, asin in picked.items():
                print(f"  {name}: {{asin: {asin}}}")
        input("Press Enter to close the browser... ")
        browser.close()
    return 0
