from itertools import product
from typing import Dict, List


def combine_dict_values(data: Dict[str, List[str]]) -> List[str]:
    # Extract all values which are lists from the dictionary
    list_values = list(data.values())

    # Generate Cartesian products of these lists
    combinations = product(*list_values)

    # Format combinations into concatenated strings
    combined_strings = ['-'.join(combination) for combination in combinations]

    return combined_strings


# Example usage:
# input_dict = {"var1": ['head', 'feet', 'nose'], "var2": ['a', 'b', 'c']}
# result = combine_dict_values(input_dict)
# print(result)
