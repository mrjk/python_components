"""Template-based variable store engine using expandvars.

This module provides template engine implementation using the expandvars library.
It extends the base template engine classes to support shell-style variable expansion
(e.g. $VAR or ${VAR}).

The main components are:

- ExpandVarsEngine: Engine for parsing and rendering templates using expandvars
- ExpandVarsInstance: Instance wrapper for template rendering

The module handles template parsing and variable substitution using shell-style
variable expansion syntax. It supports both $VAR and ${VAR} formats, with 
configurable variable symbols and strict mode.
"""

import os
import sys
import re

# pylint: disable=relative-beyond-top-level

import expandvars as _expandvars
from expandvars import expand as _expand
from expandvars import (
    ESCAPE_CHAR,
    _valid_char,
    escape,
    expand_modifier_var,
    getenv,
)  # as _expand
from .core import _TemplateEngines, _TemplateInstances


def _expand_var(vars_, nounset, environ, var_symbol):
    """Expand a single variable."""

    print("WIPPP1", vars_)

    # # sys.exit(1)
    # assert False, "WIPPP"

    if len(vars_) == 0:
        return var_symbol

    if vars_[0] == ESCAPE_CHAR:
        return var_symbol + escape(
            vars_[1:], nounset=nounset, environ=environ, var_symbol=var_symbol
        )

    if vars_[0] == var_symbol:

        # Manage chained symbols
        symbol_count = 1
        for char in vars_:
            if char == var_symbol:
                symbol_count += 1
            else:
                break

        # print("SYMBOL COUNT", symbol_count, vars_)

        # return f"{var_symbol}{var_symbol}"
        # sys.exit(1)
        # assert False, "Not implemented WIPPP"

        # return f"{var_symbol}" + expand(
        #     vars_[1:], nounset=nounset, environ=environ, var_symbol=var_symbol
        # )

        return f"{var_symbol*symbol_count}" + expand(
            vars_[symbol_count - 1 :],
            nounset=nounset,
            environ=environ,
            var_symbol=var_symbol,
        )

        # return f"{var_symbol}{var_symbol}" + expand(
        #     vars_[1:], nounset=nounset, environ=environ, var_symbol=var_symbol
        # )

        # return str(os.getpid()) + expand(
        #     vars_[1:], nounset=nounset, environ=environ, var_symbol=var_symbol
        # )

    if vars_[0] == "{":
        return expand_modifier_var(
            vars_[1:], nounset=nounset, environ=environ, var_symbol=var_symbol
        )

    print("WIPPP2", vars_, _valid_char(vars_[0]))
    m = re.match(r"([^a-zA-Z0-9]+)", vars_)
    print("MATCH", m)
    if m:
        # pprint(m.__dict__)
        junk = m.group(1)
        count = len(junk)
        # rest = m.group(2)
        # rest = None
        rest = vars_[count:]
        print("MATCHHHHHH", junk, " | ", count, " |> ", out)

        return var_symbol

        return junk + escape(
            rest, nounset=nounset, environ=environ, var_symbol=var_symbol
        )

        # if not re.match('^[a-zA-Z0-9]*', vars_[0]):
        # Invalid var name
        return var_symbol

        # return f"${var_symbol}" + expand(
        #     vars_[1:], nounset=nounset, environ=environ, var_symbol=var_symbol
        # return f"${var_symbol}" + expand(
        #     vars_[1:], nounset=nounset, environ=environ, var_symbol=var_symbol
        # )

        return var_symbol + escape(
            vars_[1:], nounset=nounset, environ=environ, var_symbol=var_symbol
        )

    buff = []
    for c in vars_:
        if _valid_char(c):
            buff.append(c)
        else:
            n = len(buff)
            return getenv(
                "".join(buff), nounset=nounset, indirect=False, environ=environ
            ) + expand(
                vars_[n:], nounset=nounset, environ=environ, var_symbol=var_symbol
            )
    return getenv("".join(buff), nounset=nounset, indirect=False, environ=environ)


_expandvars.expand_var = _expand_var

expand = _expand
# expand.expand_var = _expand_var

from pprint import pprint

# pprint(expand.__dict__)
# assert False


# =====================================================================
# TemplateEngines StringTemplate class
# =====================================================================


class ExpandVarsEngine(_TemplateEngines):
    """Python StringTemplate template engine."""

    def __init__(self):
        super().__init__()
        self.engine_cls = _expandvars.expand
        self._engine = None
        self._value = None

        self.var_symbol = "$"
        self.strict = False

    # expand(vars_, nounset=False, environ=os.environ, var_symbol="$"):

    def is_template(self, data):
        "Return true if template contains template variables"

        # Check if data is a string, otherwize we can't template it
        if not isinstance(data, str):
            return False

        # Check in Python sring.Template config if any opening pattern
        # matches in the text
        if self.var_symbol in data:
            return True
        return False

    def get_template(self, value):
        "Return a new engine instance"
        return ExpandVarsInstance(value, engine_cls=self.engine_cls)


class ExpandVarsInstance(_TemplateInstances):
    """A class that wraps a template engine instance and provides methods for"""

    def __init__(self, value, engine_cls, strict=True, symbol="$"):

        assert isinstance(value, str), "value must be a string"
        assert callable(engine_cls), "engine_cls must be a callable"
        self._value = value
        self.engine_cls = engine_cls
        self._engine = engine_cls(value)

        self.strict = strict
        self.symbol = symbol

    # Temporary disabled
    # def render_template(self, dict_vars=None, settings=None, report=None, _queryctl=None):
    def render_template(self, dict_vars=None, _queryctl=None):

        settings = _queryctl.settings

        ret = expand(
            self._value, environ=dict_vars, nounset=self.strict, var_symbol=self.symbol
        )
        return ret
