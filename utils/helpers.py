from typing import List, Mapping, Any, Iterator
import re


# String functions
# ================

# pylint: disable=redefined-builtin
def truncate(data, max=72, txt=" ..."):
    "Truncate a text to max lenght and replace by txt"
    data = str(data)
    if max < 0:
        return data
    if len(data) > max:
        return data[: max + len(txt)] + txt
    return data

# TODO: Add tests on this one
def to_domain(string, sep=".", alt="-"):
    "Transform any string to valid domain name"

    domain = string.split(sep)
    result = []
    for part in domain:
        part = re.sub("[^a-zA-Z0-9]", alt, part)
        part.strip(alt)
        result.append(part)

    return ".".join(result)



# List functions
# ==============

# TODO: Add tests on this one
def first(array):
    "Return the first element of a list or None"
    # return next(iter(array))
    array = list(array) or []
    result = None
    if len(array) > 0:
        result = array[0]
    return result

def duplicates(_list):
    """Check if given list contains duplicates"""
    known = set()
    dup = set()
    for item in _list:
        if item in known:
            dup.add(item)
        else:
            known.add(item)

    if len(dup) > 0:
        return list(dup)
    return []

def flatten(array):
    "Flatten any arrays nested arrays"
    if array == []:
        return array
    if isinstance(array[0], list):
        return flatten(array[0]) + flatten(array[1:])
    return array[:1] + flatten(array[1:])

def ordered_flatten(nested: Any, depth: int = 0) -> Iterator[Any]:
    """Flatten nested iterables while preserving ordering.

    Args:
        nested: Any potentially nested iterable structure.
        depth: Current recursion depth, used internally for debugging.

    Returns:
        Iterator[Any]: A generator yielding flattened elements in order.

    Example:
        >>> list(flatten([[1, 2], [3, 4]]))
        [1, 2, 3, 4]
    """
    try:
        # print("{}Iterate on {}".format('  '*depth, nested))
        for sublist in nested:
            for element in flatten(sublist, depth + 1):
                # print("{}got back {}".format('  '*depth, element))
                yield element
    except TypeError:
        # print('{}not iterable - return {}'.format('  '*depth, nested))
        yield nested


# Dict functions
# ==============

def merge_dicts(dict1, dict2):
    """Given two dictionaries, merge them into a new dict as a shallow copy.

    Compatibility for Python 3.5 and above"""
    # Source: https://stackoverflow.com/a/26853961/2352890
    result = dict1.copy()
    result.update(dict2)
    return result

