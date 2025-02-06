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
from pprint import pprint

import logging

# pylint: disable=relative-beyond-top-level

from .expandvars import ExpandParser, ExpandvarsException

from .core import _TemplateEngines, _TemplateInstances
from .core_engine import InvalidTemplateVarNameError


logger = logging.getLogger(__name__)


# =====================================================================
# TemplateEngines StringTemplate class
# =====================================================================


class ExpandVarsEngine(_TemplateEngines):
    """Python StringTemplate template engine."""

    def __init__(self):
        super().__init__()
        self.engine_cls = ExpandParser
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
        return ExpandVarsInstance(value, engine=self)


# pylint: disable=too-few-public-methods
class ExpandVarsInstance(_TemplateInstances):
    """A class that wraps a template engine instance and provides methods for"""

    def __init__(self, value, engine, strict=False, symbol="$"):

        assert isinstance(
            engine, _TemplateEngines
        ), "engine must be an instance of _TemplateEngines"
        assert isinstance(value, str), "value must be a string"

        self._value = value
        # self.engine = engine

        self._engine = engine.engine_cls

        self.strict = strict
        self.symbol = symbol

    def render_template(self, dict_vars=None, **_):  # _queryctl=None):
        """Render the template by expanding variables.

        Args:
            dict_vars (dict, optional): Dictionary of variables to use for
                expansion. Defaults to None.
            _queryctl (object, optional): Control object containing settings.
                Defaults to None.

        Returns:
            str: The rendered template with variables expanded.

        Note:
            This method uses the ExpandParser engine to perform Unix-style variable expansion.
            If expansion fails due to parser errors, it will return the original template value.
        """

        # settings = _queryctl.settings

        try:
            ret = self._engine(
                environ=dict_vars,
                nounset=self.strict,
                feat_pid="$$",
                var_symbol=self.symbol,
            ).expand(self._value)
        except (ExpandvarsException) as err:
            # We got a parser error here. Since we never really
            # know what is the epxected outcome, the idea is
            # ignore the error and return the original value
            logger.warning("Expandvars parser error: %s on value: %s", err, self._value)
            return self._value
        except InvalidTemplateVarNameError:
            return self._value

        return ret
