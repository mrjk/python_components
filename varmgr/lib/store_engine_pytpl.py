"""Template-based variable store engine using Python's string.Template.

This module provides template engine implementation using Python's string.Template class.
It extends the base template engine classes to support Python-style string templates 
(e.g. ${var_name} or $var_name).

The main components are:

- StringTemplate: Extended Template class with identifier extraction
- StringTemplateEngine: Engine for parsing and rendering templates
- StringTemplateInstance: Instance wrapper for template rendering

The module handles template parsing, variable substitution and validation of template
placeholders.
"""


# pylint: disable=relative-beyond-top-level

from string import Template
from .core import _TemplateEngines, _TemplateInstances, LazyDict
from .core_engine import TemplateValueError, TemplateKeyError


# =====================================================================
# Python Class overrides
# =====================================================================


class StringTemplate(Template):
    """
    String Template class override to support version of python below 3.11

    # pylint: disable=line-too-long
    Source code: Source: https://github.com/python/cpython/commit/dce642f24418c58e67fa31a686575c980c31dd37
    """

    def get_identifiers(self):
        """Returns a list of the valid identifiers in the template, in the order
        they first appear, ignoring any invalid identifiers."""

        ids = []
        # pylint: disable=invalid-name
        for mo in self.pattern.finditer(self.template):
            named = mo.group("named") or mo.group("braced")
            if named is not None and named not in ids:
                # add a named group only the first time it appears
                ids.append(named)
            elif (
                named is None
                and mo.group("invalid") is None
                and mo.group("escaped") is None
            ):
                # If all the groups are None, there must be
                # another group we're not expecting
                raise ValueError("Unrecognized named group in pattern", self.pattern)
        return ids

    def is_valid(self):
        """Returns false if the template has invalid placeholders that will cause
        :meth:`substitute` to raise :exc:`ValueError`.
        """

        # pylint: disable=invalid-name
        for mo in self.pattern.finditer(self.template):
            if mo.group("invalid") is not None:
                return False
            if (
                mo.group("named") is None
                and mo.group("braced") is None
                and mo.group("escaped") is None
            ):
                # If all the groups are None, there must be
                # another group we're not expecting
                raise ValueError("Unrecognized named group in pattern", self.pattern)
        return True

    # @classmethod
    # def is_template(cls, data):
    #     "Return true if template contains template variables"
    #     if not isinstance(data, str):
    #         return False
    #     for _ in cls.pattern.finditer(data):
    #         return True
    #     return False


# We override this method only if version of python is below 3.11
if hasattr(Template, "get_identifiers"):
    StringTemplate = Template  # noqa: F811


# =====================================================================
# TemplateEngines StringTemplate class
# =====================================================================


class StringTemplateEngine(_TemplateEngines):
    """Python StringTemplate template engine."""

    def __init__(self):
        super().__init__()
        self.engine_cls = StringTemplate
        self._engine = None
        self._value = None

    def is_template(self, data):
        "Return true if template contains template variables"

        # Check if data is a string, otherwize we can't template it
        if not isinstance(data, str):
            return False

        # Check in Python sring.Template config if any opening pattern
        # matches in the text
        for _ in self.engine_cls.pattern.finditer(data):
            return True
        return False

    def get_template(self, value):
        "Return a new engine instance"
        return StringTemplateInstance(value, engine_cls=self.engine_cls)


class StringTemplateInstance(_TemplateInstances):
    """A class that wraps a template engine instance and provides methods for
    getting variable names and rendering templates.

    This class encapsulates a template engine (like string.Template) and provides
    a consistent interface for:
    - Getting the variable names/identifiers used in the template
    - Rendering the template by substituting variables with values
    - Handling template rendering errors
    """

    def __init__(self, value, engine_cls):

        assert isinstance(value, str), "value must be a string"
        assert callable(engine_cls), "engine_cls must be a callable"
        self._value = value
        self.engine_cls = engine_cls
        self._engine = engine_cls(value)

        self.safe = False

    # Temporary disabled in favor of lazy dicts
    def get_var_names(self):
        """Return a list of the valid identifiers in the template, in the order they first
        appear, ignoring any invalid identifiers.
        """
        return self._engine.get_identifiers()

    # pylint: disable=too-many-branches
    def render_template(self, dict_vars=None, _queryctl=None):
        """Render a template by substituting variables with their values.

        Args:
            value (str): The template string to render
            dict_vars (dict): Dictionary mapping variable names to their values
            settings (Settings): Settings object containing rendering options
            report (dict, optional): Dictionary to store rendering metadata. Defaults to None.

        Returns:
            tuple: (rendered_value, report_dict) where rendered_value is the template with
                variables substituted and report_dict contains metadata about the rendering
                process

        Raises:
            TemplateValueError: If template value is invalid and settings.on_templating_error is
                Exception
            TemplateKeyError: If variable substitution fails and
                settings.on_undefined_template_error is Exception
        """
        report = _queryctl.report
        settings = _queryctl.settings
        dict_vars = dict_vars or {}
        engine = self._engine
        report = report or {}
        value = self._value

        assert isinstance(dict_vars, (dict, LazyDict)), "dict_vars must be a dict"
        assert isinstance(value, str), "value must be a string"

        # Substitute vars
        report["parse_error"] = None
        report["parsed"] = False
        err = None
        try:
            if self.safe:
                parsed = engine.safe_substitute(dict_vars)
            else:
                parsed = engine.substitute(dict_vars)
            report["parsed"] = True
        except (ValueError, KeyError) as _err:
            err = _err

            # Handle error
            report["parse_error"] = str(err)
            if isinstance(err, ValueError):
                if settings.on_templating_error is Exception:
                    raise TemplateValueError(err, value=value, report=report) from err
                if callable(settings.on_templating_error):
                    parsed = settings.on_templating_error(value, err=err, report=report)
                else:
                    parsed = settings.on_templating_error

            elif isinstance(err, KeyError):
                if settings.on_undefined_template_error is Exception:
                    raise TemplateKeyError(err, value=value, report=report) from err
                if callable(settings.on_undefined_template_error):
                    parsed = settings.on_undefined_template_error(
                        value, err=err, report=report
                    )
                else:
                    parsed = settings.on_undefined_template_error
            else:
                # Unmanaged error, raise general exception
                raise err from err

        # Build report for children
        if settings.debug:
            report["value"] = parsed
            report["raw_value"] = value

        return parsed
