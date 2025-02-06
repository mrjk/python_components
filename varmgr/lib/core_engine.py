"""Template engine core exceptions and base classes.

This module defines the core exception hierarchy for template-based variable stores.
It provides base exception classes for handling various template processing errors:

- StoreTemplateError: Base class for all template-related errors
- TemplateRenderingError: For template rendering failures 
- TemplateRenderingCircularValueError: For circular reference detection
- TemplateEngineError: For template engine failures
- TemplateValueError: For undefined variable access
- TemplateKeyError: For undefined key access

The exceptions form a hierarchy to allow specific error handling while maintaining
a common base class for all template-related errors.
"""

# pylint: disable=relative-beyond-top-level
from .store_base import VarMgrUserError


# pylint: disable=too-few-public-methods
class StoreTemplateError(VarMgrUserError):
    """Base class for StoreTemplate exceptions."""


# pylint: disable=too-few-public-methods
class TemplateRenderingError(StoreTemplateError):
    """Exception raised when template rendering fails."""


# pylint: disable=too-few-public-methods
class TemplateRenderingCircularValueError(TemplateRenderingError):
    """Exception raised when accessing a circular reference in a template."""


class TemplateEngineError(StoreTemplateError):
    """Exception raised when template engine fails."""


# pylint: disable=too-few-public-methods
class TemplateValueError(TemplateEngineError):
    """Exception raised when accessing an undefined variable in a template."""


# pylint: disable=too-few-public-methods
class TemplateKeyError(TemplateEngineError):
    """Exception raised when accessing an undefined variable in a template."""


class InvalidTemplateVarNameError(TemplateEngineError):
    """Exception raised when requesting invalid variable name.
    This error occurs when trying to access a variable with an invalid name.
    """
