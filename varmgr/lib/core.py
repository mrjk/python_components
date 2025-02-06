"""Core utilities and base classes.

This module provides core functionality used throughout the variable manager:

- LazyDict: Base class for lazy dictionary evaluation
- flatten/flatten2: Functions for flattening nested iterables
- Base exception classes for error handling

The module focuses on fundamental data structures and utilities that are used
as building blocks by other components of the variable manager.
"""

from typing import List, Mapping, Any, Iterator


def flatten2(array: List[Any]) -> List[Any]:
    """Flatten any nested arrays while preserving inner values but not ordering.

    Args:
        array: A list that may contain nested lists at any depth.

    Returns:
        List[Any]: A flattened list containing all elements from input arrays.

    Example:
        >>> flatten2([[1, 2], [3, 4]])
        [1, 2, 3, 4]
    """
    if array == []:
        return array
    if isinstance(array[0], list):
        return flatten(array[0]) + flatten(array[1:])
    return array[:1] + flatten(array[1:])


def flatten(nested: Any, depth: int = 0) -> Iterator[Any]:
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


# Top level exception classes


class VarMgrError(Exception):
    """Base class for all VarMgr exceptions.

    This class serves as the root of the VarMgr exception hierarchy.
    """

    def __init__(self, msg: str, **kwargs: Any):
        self.msg = msg
        self.kwargs = kwargs

    def __str__(self) -> str:
        prefix = f"{self.msg}"
        if self.kwargs:
            # kwargs_str = ", ".join([f"{k}={v}" for k, v in self.kwargs.items()])
            kwargs_str = ", ".join([f"{k}" for k, _ in self.kwargs.items()])
            return f"{prefix} ({kwargs_str})"
        return prefix


# Engine helpers


# pylint: disable=too-few-public-methods
class _TemplateEngines:
    """Class for managing template engines."""


# pylint: disable=too-few-public-methods
class _TemplateInstances:
    """A class that wraps a template engine instance and provides methods
    for getting variable names and rendering templates."""

    def get_var_names(self):
        """Get the names of all variables referenced in the template.

        Returns:
            list[str]: A list of variable names found in the template.
            Returns None if no variables are found.
        """

        return None


# pylint: disable=too-few-public-methods
# class LazyDict:
class LazyDict(Mapping):
    """A class that represents a lazy dictionary."""

    # Methods to implement:
    # https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes
    # Mapping
    # 	Collection
    # 	__getitem__, __iter__, __len__
    # 	__contains__, keys, items, values, get, __eq__, __ne__

    def __getitem__(self, key):
        raise NotImplementedError(f"Method not implemented: {self}.__getitem__()")

    def __iter__(self):
        raise NotImplementedError(f"Method not implemented: {self}.__iter__()")

    def __len__(self):
        raise NotImplementedError(f"Method not implemented: {self}.__len__()")

    def __contains__(self, key):
        raise NotImplementedError(f"Method not implemented: {self}.__contains__()")

    def keys(self):
        raise NotImplementedError(f"Method not implemented: {self}.keys()")

    def items(self):
        raise NotImplementedError(f"Method not implemented: {self}.items()")

    def values(self):
        raise NotImplementedError(f"Method not implemented: {self}.values()")

    def get(self, key):
        raise NotImplementedError(f"Method not implemented: {self}.get()")

    def __eq__(self, other):
        raise NotImplementedError(f"Method not implemented: {self}.__eq__()")

    def __ne__(self, other):
        raise NotImplementedError(f"Method not implemented: {self}.__ne__()")
