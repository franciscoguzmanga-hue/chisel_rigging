'''
################################################################################################################
Author: Francisco Guzman

Content: Basic utility functions for naming conventions in Maya.
Dependency: pymel.core
Maya Version tested: 2024
How to:
    - Use: Import the module and call the functions as needed.
################################################################################################################
'''

import pymel.core as pm

# Naming utility functions
def find_repeated_names() -> list[str]:
    """Search for repeated names in DAG nodes.

    Returns:
        list[str]: List of repeated names in the DAG nodes.
    """
    nodes = pm.ls("*", dag=True, long=True)
    repeated_names = [node.shortName() for node in nodes if "|" in node.shortName()]
    return list(set(repeated_names))

def convert_number_to_character(number: int) -> str:
    """Converts a non-negative integer to its corresponding Excel-style column name.

    Args:
        number (int): Number to convert.

    Raises:
        ValueError: If the number is negative.

    Returns:
        str: Excel-style column name.
    """
    if number < 0: raise ValueError("Number must be non-negative.")
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    base = len(alphabet)
    result = ''
    while number >= 0:
        result = alphabet[number % base] + result
        number = number // base - 1
    return result

def convert_character_to_number(char: str) -> int:
    """Converts an Excel-style column name to its corresponding non-negative integer.

    Args:
        char (str): Excel-style column name.

    Raises:
        ValueError: If the input string is empty or contains non-alphabetic characters.

    Returns:
        int: Corresponding non-negative integer.
    """
    if not char.isalpha(): raise ValueError("Input must be a non-empty string of alphabetic characters.")
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    base = len(alphabet)
    result = 0
    for i, c in enumerate(reversed(char.upper())):
        result += (alphabet.index(c) + 1) * (base ** i)
    return result - 1

