# -*- coding: utf-8 -*-
"""Expand system variables Unix style.

Provides functions and classes for expanding environment variables in strings using
Unix-style syntax. Supports various expansion formats including default values, error
handling, and substring operations.
"""

# pylint: disable=consider-using-f-string
# pylint: disable=raise-missing-from
# pylint: disable=dangerous-default-value
# pylint: disable=invalid-name
# pylint: disable=missing-class-docstring
# pylint: disable=line-too-long
# pylint: disable=no-else-break
# pylint: disable=too-many-branches
# pylint: disable=no-else-raise

import os
from io import TextIOWrapper

__author__ = "Arijit Basu"
__email__ = "sayanarijit@gmail.com"
__homepage__ = "https://github.com/sayanarijit/expandvars"
__description__ = "Expand system variables Unix style"
__version__ = "v0.12.0"
__license__ = "MIT"
__all__ = [
    "BadSubstitution",
    "ExpandvarsException",
    "MissingClosingBrace",
    "MissingExcapedChar",
    "NegativeSubStringExpression",
    "OperandExpected",
    "ParameterNullOrNotSet",
    "UnboundVariable",
    "expand",
    "expandvars",
]


ESCAPE_CHAR = "\\"

# Set EXPANDVARS_RECOVER_NULL="foo" if you want variables with
# `${VAR:?}` syntax to fallback to "foo" if it's not defined.
# Also works works with nounset=True.
#
# This helps with certain use cases where you need to temporarily
# disable strict parsing of critical env vars. e.g. in testing
# environment.
#
# See tests/test_recover_null.py for examples.
#
# WARNING: Try to avoid `export EXPANDVARS_RECOVER_NULL` as it
# will permanently disable strict parsing until you log out.
RECOVER_NULL = os.environ.get("EXPANDVARS_RECOVER_NULL", None)


class ExpandvarsException(Exception):
    """The base exception for all the handleable exceptions."""


class MissingClosingBrace(ExpandvarsException, SyntaxError):
    def __init__(self, param):
        super().__init__("{0}: missing '}}'".format(param))


class MissingExcapedChar(ExpandvarsException, SyntaxError):
    def __init__(self, param):
        super().__init__("{0}: missing escaped character".format(param))


class OperandExpected(ExpandvarsException, SyntaxError):
    def __init__(self, param, operand):
        super().__init__(
            "{0}: operand expected (error token is {1})".format(param, repr(operand))
        )


class NegativeSubStringExpression(ExpandvarsException, IndexError):
    def __init__(self, param, expr):
        super().__init__("{0}: {1}: substring expression < 0".format(param, expr))


class BadSubstitution(ExpandvarsException, SyntaxError):
    def __init__(self, param):
        super().__init__("{0}: bad substitution".format(param))


class ParameterNullOrNotSet(ExpandvarsException, KeyError):
    def __init__(self, param, msg=None):
        if msg is None:
            msg = "parameter null or not set"
        super().__init__("{0}: {1}".format(param, msg))


class UnboundVariable(ExpandvarsException, KeyError):
    def __init__(self, param):
        super().__init__("{0}: unbound variable".format(param))


def _valid_char(char):
    return char.isalnum() or char == "_"


def _isint(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


class ExpandParser:
    """ExpandParser for expanding Unix-style environment variables.

    A class that handles parsing and expanding environment variables in strings,
    similar to shell variable expansion. Supports various expansion modifiers
    and options.

    Args:
        nounset (bool): If True, enables strict parsing (similar to set -u / set -o nounset in bash).
            Defaults to False.
        environ (Mapping): Elements to consider during variable expansion. Defaults to os.environ.
        var_symbol (str): Character used to identify a variable. Defaults to $.
        feat_pid (bool,str): If True, enables PID expansion ($$). If string, then always return this
            hardcoded value instead. Defaults to True.

    Example:
        >>> parser = ExpandParser(environ={"PATH": "/usr/bin"})
        >>> parser.expand("$PATH:/usr/local/bin")
        '/usr/bin:/usr/local/bin'
    """

    def __init__(
        self, nounset=False, environ=os.environ, var_symbol="$", feat_pid=True
    ):
        self.nounset = nounset
        self.environ = environ
        self.var_symbol = var_symbol

        self.feat_pid = feat_pid

    def getenv(self, var, indirect=False, default=None):
        """Get value from environment variable.

        When nounset is True, it behaves like bash's "set -o nounset" or "set -u"
        and raises UnboundVariable exception.

        When indirect is True, it will use the value of the resolved variable as
        the name of the final variable.
        """
        nounset = self.nounset
        environ = self.environ

        val = environ.get(var)
        if val is not None and indirect:
            val = environ.get(val)

        if val:
            return val

        if default is not None:
            return default

        if nounset:
            if RECOVER_NULL is not None:
                return RECOVER_NULL
            raise UnboundVariable(var)
        return ""

    def escape(self, vars_):
        """Escape the first character."""
        var_symbol = self.var_symbol

        if len(vars_) == 0:
            raise MissingExcapedChar(vars_)

        if len(vars_) == 1:
            return vars_[0]

        if vars_[0] == var_symbol:
            return vars_[0] + self.expand(vars_[1:])

        if vars_[0] == ESCAPE_CHAR:
            if vars_[1] == var_symbol:
                return ESCAPE_CHAR + self.expand(vars_[1:])
            if vars_[1] == ESCAPE_CHAR:
                return ESCAPE_CHAR + self.escape(vars_[2:])

        return ESCAPE_CHAR + vars_[0] + self.expand(vars_[1:])

    # pylint: disable=too-many-return-statements
    def expand_var(self, vars_):
        """Expand a single variable."""
        var_symbol = self.var_symbol

        # Support for EoL $^
        if len(vars_) == 0:
            return var_symbol

        # Support for $\
        if vars_[0] == ESCAPE_CHAR:
            return var_symbol + self.escape(vars_[1:])

        # Support for: $$
        if vars_[0] == var_symbol:

            # Count how many $ symbols appear in sequence
            times = 2
            next = None
            for c in vars_[1:]:
                if c != var_symbol:
                    next = c
                    break
                times += 1

            if times == 2:
                # We only process pid if $$, not more.

                if self.feat_pid is True:
                    # Return process current pid
                    return str(os.getpid()) + self.expand(vars_[1:])

                if isinstance(self.feat_pid, str):
                    # Return feat_pid string
                    return self.feat_pid + self.expand(vars_[1:])

            # times = times - 1
            # If next is _valid or {, then reduce time by one
            # if next and (_valid_char(next) or next == var_symbol):
            #     print("FORWARDING", vars_[times - 1 :])
            #     return var_symbol * (times +1 ) + self.expand(vars_[times - 1 :])

            # If more than 2, then skip until next not var_symbol
            return var_symbol * times + self.expand(vars_[times - 1 :])

        # Support for: ${
        if vars_[0] == "{":
            return self._expand_modifier_var(vars_[1:])

        # Support for: $*
        buff = []
        for c in vars_:
            if _valid_char(c):
                # Support for: $[a-zA-Z0-9_]
                buff.append(c)
            else:
                # Anything else
                n = len(buff)
                if n > 0:
                    # If a valid variable name is found, expand it
                    return str(
                        self.getenv("".join(buff), indirect=False)
                    ) + self.expand(vars_[n:])

                # If the name is empty, then it's probably not a variable
                return var_symbol + self.expand(vars_)

        return self.getenv("".join(buff), indirect=False)

    def _expand_modifier_var(self, vars_):
        """Expand variables with modifier."""

        if len(vars_) <= 1:
            raise BadSubstitution(vars_)

        if vars_[0] == "!":
            indirect = True
            vars_ = vars_[1:]
        else:
            indirect = False

        buff = []
        for c in vars_:
            if _valid_char(c):
                buff.append(c)
            elif c == "}":
                n = len(buff) + 1
                return str(self.getenv("".join(buff), indirect=indirect)) + self.expand(
                    vars_[n:]
                )

            else:
                n = len(buff)
                if c == ":":
                    n += 1
                return self._expand_advanced(
                    "".join(buff), vars_[n:], indirect=indirect
                )

        raise MissingClosingBrace("".join(buff))

    def _expand_advanced(self, var, vars_, indirect=False):
        """Expand substitution."""

        if len(vars_) == 0:
            raise MissingClosingBrace(var)

        modifier = []
        depth = 1
        for c in vars_:
            if c == "{":
                depth += 1
                modifier.append(c)
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
                else:
                    modifier.append(c)
            else:
                modifier.append(c)

        if depth != 0:
            raise MissingClosingBrace(var)

        vars_ = vars_[len(modifier) + 1 :]
        modifier = self.expand("".join(modifier))

        if not modifier:
            raise BadSubstitution(var)

        if modifier[0] == "-":
            return self._expand_default(
                var, modifier=modifier[1:], set_=False, indirect=indirect
            ) + self.expand(vars_)

        if modifier[0] == "=":
            return self._expand_default(
                var, modifier=modifier[1:], set_=True, indirect=indirect
            ) + self.expand(vars_)

        if modifier[0] == "+":
            return self._expand_substitute(var, modifier=modifier[1:]) + self.expand(
                vars_
            )

        if modifier[0] == "?":
            return self._expand_strict(var, modifier=modifier[1:]) + self.expand(vars_)

        return self._expand_offset(var, modifier=modifier) + self.expand(vars_)

    def _expand_strict(self, var, modifier):
        """Expand variable that must be defined."""
        environ = self.environ

        val = environ.get(var, "")
        if val:
            return val
        if RECOVER_NULL is not None:
            return RECOVER_NULL
        raise ParameterNullOrNotSet(var, modifier if modifier else None)

    def _expand_offset(self, var, modifier):
        """Expand variable with offset."""

        buff = []
        for c in modifier:
            if c == ":":
                n = len(buff) + 1
                offset_str = "".join(buff)
                if not offset_str or not _isint(offset_str):
                    offset = 0
                else:
                    offset = int(offset_str)

                return self._expand_length(var, modifier=modifier[n:], offset=offset)

            buff.append(c)

        n = len(buff) + 1
        offset_str = "".join(buff).strip()
        if not offset_str or not _isint(offset_str):
            offset = 0
        else:
            offset = int(offset_str)
        return str(self.getenv(var, indirect=False))[offset:]

    def _expand_length(self, var, modifier, offset):
        """Expand variable with offset and length."""

        length_str = modifier.strip()
        if not length_str:
            length = None
        elif not _isint(length_str):
            if not all(_valid_char(c) for c in length_str):
                raise OperandExpected(var, length_str)
            else:
                length = None
        else:
            length = int(length_str)
            if length < 0:
                raise NegativeSubStringExpression(var, length_str)

        if length is None:
            width = 0
        else:
            width = offset + length

        return str(self.getenv(var, indirect=False))[offset:width]

    def _expand_substitute(self, var, modifier):
        """Expand or return substitute."""
        environ = self.environ

        if environ.get(var):
            return modifier
        return ""

    def _expand_default(self, var, modifier, set_, indirect):
        """Expand var or return default."""
        environ = self.environ

        if set_ and not environ.get(var):
            environ.update({var: modifier})
        return self.getenv(var, indirect=indirect, default=modifier)

    def expand(self, vars_):
        """Expand variables Unix style.

        Params:
            vars_ (str):  Variables to expand.

        Returns:
            str: Expanded values.
        """
        if isinstance(vars_, TextIOWrapper):
            # This is a file. Read it.
            vars_ = vars_.read().strip()

        if len(vars_) == 0:
            return ""

        buff = []
        var_symbol = self.var_symbol

        try:
            for c in vars_:
                if c == var_symbol:
                    n = len(buff) + 1
                    return "".join(buff) + self.expand_var(vars_[n:])

                if c == ESCAPE_CHAR:
                    n = len(buff) + 1
                    return "".join(buff) + self.escape(vars_[n:])

                buff.append(c)
            return "".join(buff)
        except MissingExcapedChar:
            raise MissingExcapedChar(vars_)
        except MissingClosingBrace:
            raise MissingClosingBrace(vars_)
        except BadSubstitution:
            raise BadSubstitution(vars_)


def expand(vars_, nounset=False, environ=os.environ, var_symbol="$", **kwargs):
    """Expand variables Unix style.

    Params:
        vars_ (str):  Variables to expand.
        nounset (bool): If True, enables strict parsing (similar to set -u / set -o nounset in bash).
        environ (Mapping): Elements to consider during variable expansion. Defaults to os.environ
        var_symbol (str): Character used to identify a variable. Defaults to $
        **kwargs: Additional keyword arguments to pass to ExpandParser.

    Returns:
        str: Expanded values.

    Example usage: ::

        from expandvars import expand

        print(expand("%PATH:$HOME/bin:%{SOME_UNDEFINED_PATH:-/default/path}", environ={"PATH": "/example"}, var_symbol="%"))
        # /example:$HOME/bin:/default/path

        # Or
        with open(somefile) as f:
            print(expand(f))
    """
    parser = ExpandParser(
        nounset=nounset, environ=environ, var_symbol=var_symbol, **kwargs
    )
    return parser.expand(vars_)


def expandvars(vars_, nounset=False, **kwargs):
    """Expand system variables Unix style.

    Params:
        vars_ (str): System variables to expand.
        nounset (bool): If True, enables strict parsing (similar to set -u / set -o nounset in bash).

    Returns:
        str: Expanded values.

    Example usage: ::

        from expandvars import expandvars

        print(expandvars("$PATH:$HOME/bin:${SOME_UNDEFINED_PATH:-/default/path}"))
        # /bin:/sbin:/usr/bin:/usr/sbin:/home/you/bin:/default/path

        # Or
        with open(somefile) as f:
            print(expandvars(f))
    """
    return expand(vars_, nounset=nounset, **kwargs)
