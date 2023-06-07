from typing import Iterable, List

def combo_sums(T: int or float,
               options: Iterable[int or float],
               max_length: int or None = None) -> List[List[int or float]]:
    combinations = []

    # Helper function to recursively find combinations
    def find_combinations(target, current_combination, index):
        if target == 0:
            # Sum matches the target, add current combination to the list
            combinations.append(current_combination)
            return

        if target < 0 or index >= len(options):
            # Target exceeded or no more options available
            return

        option = options[index]

        # Include the current option in the combination
        find_combinations(target - option, current_combination + [option], index)

        # Skip the current option and move to the next one
        find_combinations(target, current_combination, index + 1)

    # Start the recursion
    find_combinations(T, [], 0)

    if max_length:
        return [combo for combo in combinations if len(combo) <= max_length]

    return combinations

