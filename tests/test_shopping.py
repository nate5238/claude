import unittest
from pathlib import Path

from mealplan.library import Ingredient, load_library
from mealplan.shopping import build_shopping_list, normalize_unit

ROOT = Path(__file__).resolve().parent.parent

NOODLES = "cold-rice-noodles-with-chicken-and-peanut-sauce"
MISO_SALMON = "maple-miso-sheet-pan-salmon"
FETA = "sheet-pan-feta-with-chickpeas-and-tomatoes"
COCONUT = "sticky-coconut-chicken-and-rice"
HAND_ROLLS = "soy-glazed-salmon-hand-rolls"


class ShoppingListTest(unittest.TestCase):
    def setUp(self):
        self.library = load_library(ROOT)

    def by_name(self, shopping):
        return {i.item: i for i in shopping.items + shopping.pantry_check}

    def test_merges_same_item_across_recipes(self):
        items = self.by_name(build_shopping_list(self.library, {NOODLES: 1, MISO_SALMON: 1}, {}))
        self.assertEqual(items["limes"].qty, 8)
        self.assertEqual(
            items["limes"].used_in,
            ["Cold Rice Noodles With Grilled Chicken and Peanut Sauce", "Maple and Miso Sheet-Pan Salmon With Green Beans"],
        )

    def test_batches_multiply_and_units_convert(self):
        items = self.by_name(build_shopping_list(self.library, {MISO_SALMON: 2}, {}))
        self.assertEqual((items["salmon fillet"].qty, items["salmon fillet"].unit), (3, "lb"))
        self.assertEqual((items["green beans"].qty, items["green beans"].unit), (2, "lb"))
        self.assertEqual(items["rice vinegar"].unit, "tbsp")

    def test_cups_merge_into_one_package(self):
        items = self.by_name(build_shopping_list(self.library, {COCONUT: 1, HAND_ROLLS: 1}, {}))
        rice = items["short-grain rice"]
        self.assertEqual((rice.qty, rice.unit, rice.cart_qty), (3, "cup", 1))

    def test_pantry_staples_are_kept_out_of_cart(self):
        shopping = build_shopping_list(self.library, {FETA: 1}, {})
        self.assertNotIn("olive oil", {i.item for i in shopping.items})
        self.assertIn("olive oil", {i.item for i in shopping.pantry_check})

    def test_product_pins_apply(self):
        items = self.by_name(build_shopping_list(self.library, {NOODLES: 1}, {}))
        self.assertEqual(items["thai chiles"].cart_qty, 1)
        self.assertEqual(items["persian cucumbers"].cart_qty, 2)
        self.assertEqual(items["boneless skinless chicken thighs"].category, "Meat & Seafood")

    def test_snacks_and_extras(self):
        shopping = build_shopping_list(
            self.library, {}, {"trail-mix": 2}, [Ingredient(item="coffee beans")]
        )
        items = self.by_name(shopping)
        self.assertEqual(items["trail mix"].cart_qty, 2)
        self.assertEqual(items["coffee beans"].used_in, ["extra"])

    def test_unknown_recipe_is_an_error(self):
        with self.assertRaises(KeyError):
            build_shopping_list(self.library, {"lasagna": 1}, {})

    def test_pinch_merges_with_teaspoons(self):
        items = self.by_name(build_shopping_list(self.library, {MISO_SALMON: 1, FETA: 1}, {}))
        flakes = items["red-pepper flakes"]  # a pinch + 1/2 tsp
        self.assertEqual((flakes.qty, flakes.unit), (0.56, "tsp"))

    def test_garlic_cloves_buy_one_head(self):
        items = self.by_name(build_shopping_list(self.library, {NOODLES: 1}, {}))
        self.assertEqual((items["garlic"].qty, items["garlic"].unit, items["garlic"].cart_qty), (5, "clove", 1))

    def test_unit_aliases(self):
        self.assertEqual(normalize_unit("Pounds"), "lb")
        self.assertEqual(normalize_unit("Tablespoons"), "tbsp")
        self.assertEqual(normalize_unit("cans"), "can")


if __name__ == "__main__":
    unittest.main()
