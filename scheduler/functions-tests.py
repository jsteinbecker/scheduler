from scheduler.functions import combo_sums
from django.test import TestCase


class TestComboSums(TestCase):
    def test_basic(self):
        """
        Test combo_sums function
        ===========================
        """
        total   = 40
        options = [4, 8, 10]

        combos = combo_sums(total, options)

        print("\n".join([line.lstrip() for line in self.test_basic.__doc__.splitlines()]))
        print(f"TOTAL:   {total}")
        print(f"OPTIONS: {options}\n")
        print(f"COMBOS:  {len(combos)}")
        for combo in combos:
            print(combo)
        print("_" * 20)

    def test_with_max_length(self):
        """
        Test combo_sums function with max_length
        ===========================
        """
        total   = 40
        options = [4, 8, 10]
        max_length = 5

        combos = combo_sums(total, options, max_length)

        print("\n".join([line.lstrip() for line in self.test_with_max_length.__doc__.splitlines()]))
        print(f"TOTAL: {total}")
        print(f"OPTIONS: {options}")
        print(f"--- LIMIT TO MAX_LENGTH: {max_length} ---")
        print(f"COMBOS: {len(combos)}")
        for combo in combos:
            print(combo)
        print("_" * 20)

        total = 40
        options = [7, 8, 10, 12]
        max_length = 5

        combos = combo_sums(total, options, max_length)

        print("\n".join([line.lstrip() for line in self.test_with_max_length.__doc__.splitlines()]))
        print(f"TOTAL: {total}")
        print(f"OPTIONS: {options}")
        print(f"--- LIMIT TO MAX_LENGTH: {max_length} ---")
        print(f"COMBOS: {len(combos)}")
        for combo in combos:
            print(combo)
        print("_" * 20)

    def test_with_range(self):
        """
        Test combo_sums function with range
        ===========================
        """
        collection = []
        for i in [28,30,32,34,36,38,40,42]:
            total   = i
            options = [8, 10]
            max_length = 5

            combos = combo_sums(total, options, max_length)

            collection.append(combos)

        for c in collection:
            print(f"total: {sum(c[0])} \t combos: {len(c)} \t {c}")



