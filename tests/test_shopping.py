import unittest
from pathlib import Path

from mealplan.library import Ingredient, load_library
from mealplan.shopping import build_shopping_list, normalize_unit

ROOT = Path(__file__).resolve().parent.parent


class ShoppingListTest(unittest.TestCase):
    def setUp(self):
        self.library = load_library(ROOT)

    def by_name(self, shopping):
        return {i.item: i for i in shopping.items + shopping.pantry_check}

    def test_merges_same_item_across_recipes(self):
        items = self.by_name(build_shopping_list(self.library, {"chicken-tacos": 1, "sheet-pan-salmon": 1}, {}))
        self.assertEqual(items["limes"].qty, 3)
        self.assertEqual(items["limes"].used_in, ["Chicken Tacos", "Sheet Pan Salmon & Veggies"])

    def test_batches_multiply_and_units_convert(self):
        items = self.by_name(build_shopping_list(self.library, {"overnight-oats": 2}, {}))
        self.assertEqual((items["rolled oats"].qty, items["rolled oats"].unit), (4, "cup"))
        self.assertEqual((items["blueberries"].qty, items["blueberries"].unit), (12, "oz"))
        self.assertEqual(items["chia seeds"].unit, "cup")  # 4 tbsp -> 0.25 cup

    def test_pantry_staples_are_kept_out_of_cart(self):
        shopping = build_shopping_list(self.library, {"chicken-tacos": 1}, {})
        self.assertNotIn("olive oil", {i.item for i in shopping.items})
        self.assertIn("olive oil", {i.item for i in shopping.pantry_check})

    def test_product_pins_apply(self):
        items = self.by_name(build_shopping_list(self.library, {"chicken-tacos": 1}, {}))
        self.assertEqual(items["corn tortillas"].cart_qty, 1)
        self.assertEqual(items["avocado"].cart_qty, 2)
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

    def test_unit_aliases(self):
        self.assertEqual(normalize_unit("Pounds"), "lb")
        self.assertEqual(normalize_unit("Tablespoons"), "tbsp")
        self.assertEqual(normalize_unit("cans"), "can")


if __name__ == "__main__":
    unittest.main()
