from itertools import product
from typing import Dict, List


def get_treatments(variables: Dict[str, List[str]]) -> List[str]:
    # Extract all values which are lists from the dictionary
    list_values = list(variables.values())

    # Generate Cartesian products of these lists
    combinations = product(*list_values)

    # Format combinations into concatenated strings
    combined_strings = ["-".join(combination) for combination in combinations]

    return combined_strings
