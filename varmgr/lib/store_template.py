"""Template-based variable store implementation.

This module provides template-based variable resolution capabilities by extending the base 
StoreManager. It allows variables to be defined using string templates (e.g. ${var_name}) 
which are resolved at runtime.

The main components are:

- StringTemplate: Extended Template class with identifier extraction
- StringTemplateEngine: Engine for parsing and rendering templates 
- RenderableStoreManager: Store manager with template rendering capabilities
- RenderingSettings: Configuration for template rendering behavior

The module handles template parsing, variable substitution, error handling and caching of rendered 
values.
"""

# pylint: disable=relative-beyond-top-level


# from string import Template
from typing import Any, Optional
import logging
from pprint import pprint
from dataclasses import dataclass

# from .common import
from .core import LazyDict

from .store_base import StoreManager, UndefinedVarError
from .store_engine_pytpl import StringTemplateEngine
from .store_engine_expandvars import ExpandVarsEngine
from .core_engine import (
    TemplateRenderingCircularValueError,
    # TemplateRenderingError,
    # TemplateValueError,
    # TemplateKeyError,
    InvalidTemplateVarNameError,
)

logger = logging.getLogger(__name__)
# try:
#     old_value = value
#     value = tpl.substitute(**env)
#     if old_value != value:
#         self.log.trace(
#             f"Transformed template var {hint}: {old_value} => {value}"
#         )


# =====================================================================
# Renderer class
# =====================================================================


@dataclass
class RenderingSettings:
    """Class for keeping track of template settings."""

    # on_undefined_error: Any = Exception
    on_templating_error: Any = Exception
    on_undefined_error: Any = Exception
    on_undefined_template_error: Any = Exception
    template: bool = True
    debug: bool = False
    cache: bool = True


# pylint: disable=too-few-public-methods
class QueryCtl:
    """Class for controlling query process."""

    def __init__(self, key_ctl, parent=None, settings=None, report=None):

        self.key_ctl = key_ctl
        self.parent = parent or None
        self.settings = settings
        self.report = report or {}
        self.children = {}

        self.seen = []
        self.lvl = 0

        # Auto bind to parent if provided
        if parent is None:

            # Automatic setting conversion
            if isinstance(self.settings, dict):
                self.settings = RenderingSettings(**self.settings)

        else:
            # if parent is not None:

            assert isinstance(parent, QueryCtl), "parent must be a QueryCtl instance"

            assert settings is None, "settings must be None when parent is provided"
            self.settings = parent.settings

            self.lvl = parent.lvl + 1
            parent.children[key_ctl] = self

    def is_not_circular(self, key=None, raise_error=True):
        """Check if there is a circular reference in the query control chain.

        Walks up the parent chain checking if the given key (or self.key_ctl if key=None)
        appears more than once, which would indicate a circular reference.

        Args:
            key (str, optional): Key to check for circular reference. Defaults to self.key_ctl.
            raise_error (bool, optional): Whether to raise an error if circular reference found.
                                        Defaults to True.

        Returns:
            bool: True if no circular reference found, False if circular reference found and
                  raise_error=False.

        Raises:
            TemplateRenderingCircularValueError: If circular reference found and raise_error=True.
        """

        if self.parent is None:
            return True

        key = self.key_ctl
        key_stack = [key]

        curr_parent = self.parent
        while curr_parent is not None:
            curr_key = curr_parent.key_ctl
            key_stack.append(curr_key)
            if curr_key == key:
                loop = " -> ".join(key_stack)
                msg = f"Circular reference detected on '{key}': {loop}"
                if raise_error:
                    raise TemplateRenderingCircularValueError(
                        msg, key=key, stack=key_stack
                    )
                # else:
                return False

            # Iterate on parent
            curr_parent = curr_parent.parent

        return True


# Methods to implement:
# https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes
# Mapping
# 	Collection
# 	__getitem__, __iter__, __len__
# 	__contains__, keys, items, values, get, __eq__, and __ne__


class LazyQueryDict(LazyDict):
    """A class that represents a lazy dictionary."""

    def __init__(self, renderer, settings=None, _queryctl=None, report=None):
        self.renderer = renderer
        self.settings = settings
        self._queryctl = _queryctl
        self.report = report or {}

    # Public API
    def __getitem__(self, key):
        try:
            return self._get_item(key)
        except KeyError as err:
            raise KeyError(f"LazyDict: getitem failed for {key}: {err}") from err
        # except Exception as err:
        #     raise Exception(f"BUG SKIPPED ECEPTION: {err}") from err

    def __len__(self):
        return 1

    def get(self, key):
        "Like dict.get() method"
        return self._get_item(key)

    # Internal API
    def _get_item(
        self,
        key,
        report=None,
    ):

        if not key:
            # raise KeyError(f"LazyDict: getitem got empty key name: key={key}, {self.renderer}")
            raise InvalidTemplateVarNameError(
                f"LazyDict: getitem got empty key name: key={key}, {self.renderer}"
            )

        report = report or {}
        _queryctl = self._queryctl

        print("RECURSIVE QUERY", key)

        # Ensure not circular
        _queryctl.is_not_circular()

        assert _queryctl is not None, "QueryCtl is required"
        _queryctl.lvl += 1
        ret = self.renderer.render_var(
            key,
            # settings=self.settings,
            # report=report,
            _parent_queryctl=_queryctl,
        )
        _queryctl.lvl -= 1

        if self.settings.debug:
            _report = ret[1]
            ret = ret[0]

        self._queryctl.seen.append(key)
        return ret


ENGINES = {
    "expandvars": ExpandVarsEngine,
    "py_stringtemplate": StringTemplateEngine,
}


class Renderer:
    """A class that renders template variables by resolving references.

    The Renderer class handles resolving template variables in a given scope,
    processing any nested references and caching results for efficiency.

    Args:
        store: The variable store containing the values to render.
        scope: The scope name to limit variable resolution.
    """

    def __init__(self, store, scope: str, engine: str = None):
        self.store = store
        self.scope = scope
        self._cache = {}

        self.sources = store.get_ordered_sources(scope=scope)

        if engine:
            self.engine = ENGINES[engine]()
        else:
            # WIP TO FIX
            # self.engine = ENGINES["py_stringtemplate"]()
            self.engine = ENGINES["expandvars"]()

    def render_values(self, **kwargs):
        """Get all variables and their rendered values.

        This method retrieves all variables in the current scope and renders their values,
        resolving any template references. The rendered values can be cached to avoid
        redundant processing.

        Args:
            cache: Whether to cache rendered values for reuse. Defaults to True.

        Returns:
            Dict[str, Any]: Dictionary mapping variable names to their rendered values.
        """

        _out = {}
        for var_name in self.store.get_var_names(scope=self.scope):
            _out[var_name] = self.render_var(var_name, **kwargs)

        return _out

    # pylint: disable=too-many-arguments
    def render_var(
        self,
        var_name: str,
        debug=False,
        cache=True,
        settings=None,
        template=True,
        _parent_queryctl=None,
        _lvl=None,
        **kwargs_settings,
    ) -> str:
        """Render a variable value, resolving any template references.

        This method retrieves the value of a variable and processes any template
        references (variables enclosed in curly braces) within it. It handles nested
        references recursively and can cache results for better performance.

        Args:
            var_name: Name of the variable to render.
            debug: Whether to return additional debug information.
            cache: Whether to cache rendered values for reuse.
            settings: RenderingSettings instance to control error handling and behavior.
                     If None, default settings will be used.

        Returns:
            str: The rendered variable value with all template references resolved.
            If debug=True, returns a tuple of (value, debug_info).

        Raises:
            UndefinedVarError: If the variable or any referenced variables don't exist
                              and settings.on_undefined_error is Exception.
            ValueError: If circular references are detected.
            TemplateUndefinedVarError: If a variable is undefined and
                                      settings.on_undefined_error is Exception.
        """

        assert var_name, f"Got empty var_name: {var_name}"

        # 0. Init report
        _report = {
            "key": var_name,
            # "level": _queryctl.lvl,
            "parsed": False,
            "cache": False,
            "cached": False,
        }
        # print("RENDERER: ", _lvl, var_name)

        # Prepare QueryCtl Settings
        local_settings = None
        if _parent_queryctl is None:
            local_settings = settings or {
                "on_templating_error": lambda value, err=None, report=None: value,
                "on_undefined_error": Exception,
                "on_undefined_template_error": lambda value, **_: value,
                "debug": debug,
                "cache": cache,
                "template": template,
            }
            local_settings.update(kwargs_settings)

        # if _parent_queryctl is None:
        _queryctl = QueryCtl(
            key_ctl=var_name,
            parent=_parent_queryctl,
            settings=local_settings,
            report=_report,
        )

        _report["level"] = _queryctl.lvl

        # Fetch settings from queryctl
        assert isinstance(
            _queryctl.settings, RenderingSettings
        ), "settings must be a RenderingSettings instance"
        debug = _queryctl.settings.debug
        cache = _queryctl.settings.cache

        logger.info("Renderer: Rendering var%d: %s", _queryctl.lvl, var_name)

        # 3. Check cache
        if cache and var_name in self._cache:
            out = self._cache[var_name]
            _report["cache"] = True
            if debug:
                return out, _report
            return out

        # 4. Process var
        value = self.render_var_process(
            var_name,
            _queryctl=_queryctl,
            report=_report,
        )

        # 5. Save in cache
        if cache:
            self._cache[var_name] = value
            _report["cached"] = True

        # 6. Return value
        if debug:
            return value, _report
        return value

    def render_var_process(
        self,
        var_name,
        #    settings=None,
        report=None,
        _queryctl=None,
    ):
        "Actually process the variable, but without cache"

        settings = _queryctl.settings
        # _report = _queryctl.report
        _report = report or {}
        print("\n\nRENDER_VAR_PROCESS", var_name)

        # 1. Fetch and process variable
        try:
            value = self.store.get_value(var_name, scope=self.scope)
        except UndefinedVarError as err:

            if settings.on_undefined_error is Exception:
                raise err
            if callable(settings.on_undefined_error):
                value = settings.on_undefined_error(var_name, err=err, report=_report)
            else:
                value = settings.on_undefined_error

            # msg = f"Undefined variable {var_name} in scope {self.scope}"
            # print("RAISE ERROR", self, msg)
            # # pylint: disable=raise-missing-from
            # raise UndefinedVarError(
            #     msg,
            #     report=_report,
            #     # err=err,
            # )  # from err
        _report["value"] = value
        _report["parsed"] = False
        _report["templated"] = False

        # 2. Process template variables, if possible/requested
        tpl_engine = self.engine
        if not settings.template:
            _report["templatable"] = "disabled"
            return value

        if not tpl_engine.is_template(value):
            _report["templatable"] = False
            return value

        _report["templatable"] = True

        # Inject text into template engine
        template = tpl_engine.get_template(value)

        # Fetch template variable names from string
        # and recursively resolve template variables values
        # If no variable names found, then simply skip templating
        dict_vars = LazyQueryDict(self, settings=settings, _queryctl=_queryctl)

        # if len(dict_vars) > 0:
        # Try to parse value with dict_vars
        _report["templated"] = True
        # try:
        value = template.render_template(
            dict_vars=dict_vars,
            _queryctl=_queryctl,
        )

        return value


# pylint: disable=too-few-public-methods
class RenderableStoreManager(StoreManager):
    """
    A class to manage variables and their sources.
    """

    def __init__(self):
        self._renderer_cache = {}

        super().__init__()

    def get_renderer(self, scope_name: Optional[str] = None) -> Renderer:
        """Get or create a Renderer instance for the given scope.

        Args:
            scope_name (Optional[str], optional): The scope name to get a renderer for.
                If None, uses the default scope. Defaults to None.

        Returns:
            Renderer: A Renderer instance configured for the specified scope.
                The same instance will be returned for subsequent calls with the same scope.
        """

        # scope_name = scope_name or "default"

        # Return from cache
        if scope_name and scope_name in self._renderer_cache:
            return self._renderer_cache[scope_name]

        # Create and save object
        renderer = Renderer(store=self, scope=scope_name)
        self._renderer_cache[scope_name] = renderer
        return renderer
