
import re
from typing import List
from unidecode import unidecode

def optimize_list(numbers: List[int]):
    """Optimize a list of numbers to a list of ranges.

    When highlighting lines in a code block, LaTeX understands
    a more compact format for ranges. This function converts
    the highlighted lines into a compact format.

    >>> optimize_list([1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 14, 15, 16])
    ['1-6', '8-10', '12', '14-16']
    """
    if not numbers:
        return []

    numbers = sorted(numbers)
    optimized = []
    start = end = numbers[0]

    for num in numbers[1:]:
        if num == end + 1:
            end = num
        else:
            optimized.append(f"{start}-{end}" if start != end else str(start))
            start = end = num

    optimized.append(f"{start}-{end}" if start != end else str(start))
    return optimized

def to_kebab_case(name):
    """Converts a string to kebab case
    >>> to_kebab_case("Hello World")
    'hello-world'
    >>> to_kebab_case("Hello World!")
    'hello-world'
    >>> to_kebab_case("L'abricot")
    'l-abricot'
    >>> to_kebab_case("Éléphant")
    'elephant'
    """
    name = unidecode(name)
    name = re.sub(r"[^\w\s']", "", name)
    name = re.sub(r"[\s']+", "-", name)
    return name.lower()


def escape_latex_chars(text):
    """Escape LaTeX special characters.

    >>> escape_latex_chars("Hello & {World}")
    'Hello \\& \\{World\\}'
    """

    mapping = [
        ("&", r"\&"),
        ("%", r"\%"),
        ("#", r"\#"),
        ("$", r"\$"),
        ("_", r"\_"),
        ("^", r"\^"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("\\", r"\textbackslash{}"),
    ]
    return "".join([c if c not in dict(mapping) else dict(mapping)[c] for c in text])
