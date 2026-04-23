import pytest

from utils.calculations import convert_50_to_100, convert_100_to_50, get_multiplication_result, hydro_calc


class TestConvert50to100:

    def test_basic_conversion(self):
        """Стандартный тест:
         пропорции закваски: 20,20,40
         поставлены в опаре 1:1:1."""
        result = convert_50_to_100(
            starter_50=20, water_50=20, flour_50=40,
            starter_part=1, water_part=1, flour_part=1
        )
        # Общий вес опары 50% = 80. sourdough100 = (80/3)*4 ≈ 106.7
        # sum_of_parts = 3, part ≈ 35.6
        assert result["total_weight"] == round((80/3)*4, 1)
        assert result["starter"] == round((80/3)*4/3, 1)
        assert result["water"] == round((80/3)*4/3, 1)
        assert result["flour"] == round((80/3)*4/3, 1)
        assert result["water_to_remove"] == round(80/3, 1)

    def test_unequal_parts(self):
        """Пропорция 1:2:2."""
        result = convert_50_to_100(
            starter_50=30, water_50=30, flour_50=60,
            starter_part=1, water_part=2, flour_part=2
        )
        total_weight50 = 120
        expected_sourdough100 = (total_weight50 / 3) * 4  # 160
        sum_of_parts = 5
        part = expected_sourdough100 / sum_of_parts  # 32

        assert result["total_weight"] == round(expected_sourdough100, 1)
        assert result["starter"] == round(part * 1, 1)
        assert result["water"] == round(part * 2, 1)
        assert result["flour"] == round(part * 2, 1)
        assert result["water_to_remove"] == round(total_weight50 / 3, 1)


class TestConvert100to50:

    def test_basic_conversion(self):
        """Стандартный тест с пропорцией 1:1:1."""
        result = convert_100_to_50(
            starter_100=20, water_100=40, flour_100=40,
            starter_part=1, water_part=1, flour_part=1
        )
        total_weight100 = 100
        expected_sourdough50 = (total_weight100 / 4) * 3  # 75
        sum_of_parts = 3
        part = expected_sourdough50 / sum_of_parts  # 25

        assert result["total_weight"] == round(expected_sourdough50, 1)
        assert result["starter"] == round(part, 1)
        assert result["water"] == round(part, 1)
        assert result["flour"] == round(part, 1)
        assert result["water_to_add"] == round(total_weight100 / 4, 1)

    def test_unequal_parts(self):
        """Пропорция 1:2:2."""
        result = convert_100_to_50(
            starter_100=30, water_100=60, flour_100=60,
            starter_part=1, water_part=2, flour_part=2
        )
        total_weight100 = 150
        expected_sourdough50 = (total_weight100 / 4) * 3  # 112.5
        sum_of_parts = 5
        part = expected_sourdough50 / sum_of_parts  # 22.5

        assert result["total_weight"] == round(expected_sourdough50, 1)
        assert result["starter"] == round(part * 1, 1)
        assert result["water"] == round(part * 2, 1)
        assert result["flour"] == round(part * 2, 1)
        assert result["water_to_add"] == round(total_weight100 / 4, 1)

class TestGetMultiplicationResult:

    @pytest.fixture
    def sample_recipe(self):
        return {
            "groups": [
                {
                    "name": "Тесто",
                    "ingredients": [
                        {"name": "мука", "amount": 500, "unit": "г."},
                        {"name": "вода", "quantity": 350, "unit": "мл."},
                        {"name": "соль", "amount": 10, "unit": "г."},
                    ]
                }
            ]
        }



    def test_basic_multiplication(self, sample_recipe):
        """Умножение на целое число."""
        result = get_multiplication_result(2, sample_recipe)
        ingredients = result["groups"][0]["ingredients"]
        assert ingredients[0]["amount"] == 1000  # 500 * 2
        assert ingredients[1]["amount"] == 700  # 350 * 2
        assert ingredients[2]["amount"] == 20     # 10 * 2

    def test_multiplication_by_fraction(self, sample_recipe):
        """Умножение на дробное число (половина)."""
        result = get_multiplication_result(0.5, sample_recipe)
        ingredients = result["groups"][0]["ingredients"]
        assert ingredients[0]["amount"] == 250.0  # 500 * 0.5
        assert ingredients[1]["amount"] == 175.0  # 350 * 0.5
        assert ingredients[2]["amount"] == 5       # 10 * 0.5

class TestHydroCalc:

    @pytest.fixture
    def sample_recipe(self):
        """Рецепт с группами 'Сухие' и 'Жидкие'."""
        return {
            "data": {
                "title": "ХЛЕБ",
                "groups": [
                    {
                        "name": "Сухие",
                        "ingredients": [
                            {"name": "мука", "quantity": 500, "unit": "г."},
                            {"name": "соль", "quantity": 10, "unit": "г."},
                        ]
                    },
                    {
                        "name": "Жидкие",
                        "ingredients": [
                            {"name": "вода", "quantity": 350, "unit": "мл."},
                        ]
                    }
                ]
            }
        }

    def test_basic_hydration(self, sample_recipe):
        """Стандартный расчёт: 500+10=550 сухих, 350 жидких → (350/550)*100 ≈ 63.6%."""
        hydro, dry_sum, wet_sum = hydro_calc(sample_recipe)
        assert dry_sum == 510  # 500 + 10
        assert wet_sum == 350
        assert hydro == round((350 / 510) * 100, 1)  # ≈ 68.6

    def test_only_dry_ingredients(self):
        """Только сухие ингредиенты — гидрация 0."""
        recipe = {
            "data": {
                "groups": [
                    {
                        "name": "Сухие",
                        "ingredients": [
                            {"name": "мука", "quantity": 500, "unit": "г."},
                        ]
                    }
                ]
            }
        }
        hydro, dry_sum, wet_sum = hydro_calc(recipe)
        assert dry_sum == 500
        assert wet_sum == 0
        assert hydro == 0.0  # 0/500 * 100 = 0

    def test_only_wet_ingredients(self):
        """Только жидкие ингредиенты — ValueError (деление на ноль)."""
        recipe = {
            "data": {
                "groups": [
                    {
                        "name": "Жидкие",
                        "ingredients": [
                            {"name": "вода", "quantity": 350, "unit": "мл."},
                        ]
                    }
                ]
            }
        }
        with pytest.raises(ZeroDivisionError):
            hydro_calc(recipe)

    def test_mixed_case_group_names(self):
        """Названия групп в разном регистре (Сухие, сухие, СУХИЕ)."""
        recipe = {
            "data": {
                "groups": [
                    {
                        "name": "СУХИЕ",
                        "ingredients": [
                            {"name": "мука", "quantity": 300, "unit": "г."},
                        ]
                    },
                    {
                        "name": "жидкие",
                        "ingredients": [
                            {"name": "вода", "quantity": 200, "unit": "мл."},
                        ]
                    }
                ]
            }
        }
        hydro, dry_sum, wet_sum = hydro_calc(recipe)
        assert dry_sum == 300
        assert wet_sum == 200
        assert hydro == round((200 / 300) * 100, 1)

    def test_ignores_other_groups(self):
        """Группы не 'Сухие' и не 'Жидкие' игнорируются."""
        recipe = {
            "data": {
                "groups": [
                    {
                        "name": "Опара",
                        "ingredients": [
                            {"name": "мука", "quantity": 999, "unit": "г."},
                        ]
                    },
                    {
                        "name": "Сухие",
                        "ingredients": [
                            {"name": "мука", "quantity": 500, "unit": "г."},
                        ]
                    }
                ]
            }
        }
        hydro, dry_sum, wet_sum = hydro_calc(recipe)
        assert dry_sum == 500  # Только из "Сухие", "Опара" игнорируется