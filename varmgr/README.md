# Variable Manager (varmgr)

A powerful and flexible variable management system that provides hierarchical configuration management with scoping, layering, and variable resolution capabilities.


## Table of Contents

- [Goal](#goal)
- [Technical Implementation Overview](#technical-implementation-overview)
- [Core Concepts](#core-concepts)
    - [1. Sources](#1-sources)
    - [2. Scopes](#2-scopes)
    - [3. Variable Resolution](#3-variable-resolution)
- [Quickstart](#quickstart)
- [Basic Usage](#basic-usage)
- [Template Variables](#template-variables)
- [Working with Multiple Scopes](#working-with-multiple-scopes)
- [Debugging and Inspection](#debugging-and-inspection)
- [Advanced Variable Usage](#advanced-variable-usage)
    - [1. Variable Combinations and Nesting](#1-variable-combinations-and-nesting)
    - [2. Special Characters and Edge Cases](#2-special-characters-and-edge-cases)
- [Common Exceptions and Error Cases](#common-exceptions-and-error-cases)
    - [1. Circular References](#1-circular-references)
    - [2. Undefined Variables](#2-undefined-variables)
    - [3. Malformed Templates](#3-malformed-templates)


## Goal

The Variable Manager solves the common problem of managing configuration variables across different scopes and layers in complex applications. It addresses several key challenges:

- Managing configuration variables across different scopes (application, project, stack)
- Handling variable overrides and fallbacks in a predictable way
- Supporting variable resolution with dependencies
- Providing a clear hierarchy for configuration sources
- Enabling flexible configuration through multiple sources (CLI, environment, config files, etc.)

## Requirements

* Python 3.11
* expandvars:
    * Fork: `pip install git+https://github.com/mrjk/expandvars.git@develop`
    * Contains some bugfixes and more options

## Technical Implementation Overview

### Core Concepts

#### 1. Sources

Sources represent different configuration origins with assigned priority levels. Each source has:
- A unique name (e.g., `app_cli`, `project_env`)
- A priority level (lower numbers = higher priority)
- Optional help text describing its purpose

Example source definition:
```python
Source("app_cli", level=300, help="Application main CLI")
Source("app_env", level=300, help="Application environment variables")
Source("app_defaults", level=999, help="Application defaults")
```

#### 2. Scopes

Scopes define hierarchical configuration contexts that can inherit from each other. The system supports three main scopes:

- `scope_app`: Application-level configuration
- `scope_project`: Project-level configuration (inherits from app)
- `scope_stack`: Stack-level configuration (inherits from project)

Each scope can access variables from its own sources and inherited scopes.

#### 3. Variable Resolution

The system provides two main implementations:

1. `StoreManager`: Basic variable resolution with scope inheritance
2. `RenderableStoreManager`: Advanced variable resolution supporting template variables (e.g., `${var_name}`)

## Quickstart

### Basic Usage

```python
from lib.store import StoreManager, Source

# Create a variable manager instance
varmgr = StoreManager()

# Define and add sources
varmgr.add_sources([
    Source("app_cli", level=300, help="Application main CLI"),
    Source("app_env", level=300, help="Application environment variables"),
    Source("app_defaults", level=999, help="Application defaults"),
])

# Define scopes and their inheritance
varmgr.set_scopes({
    "scope_app": ["app_cli", "app_env", "app_defaults"],
    "scope_project": [
        "project_cli",
        "project_env",
        "project_defaults",
        "scope_app",  # Inherit from app scope
    ],
})

# Set configuration values
app_config = {
    "app_name": "myapp",
    "debug": True
}
varmgr.set_layer("app_cli", app_config)

# Get values
app_name = varmgr.get_value("app_name")  # Returns "myapp"
```

### Template Variables

Using the `RenderableStoreManager` for variable interpolation:

```python
from lib.store_template import RenderableStoreManager

# Create a renderable store manager
varmgr = RenderableStoreManager()

# Set up sources and scopes (same as basic usage)
# ...

# Set values with templates
config = {
    "project_name": "myproject",
    "env": "prod",
    "stack_name": "${project_name}-${env}"  # Will resolve to "myproject-prod"
}

varmgr.set_layer("project_env", config)

# Get rendered values
stack_name = varmgr.get_value("stack_name")  # Returns "myproject-prod"
```

### Working with Multiple Scopes

```python
# Set values in different scopes
app_vars = {
    "log_level": "INFO",
    "app_name": "myapp"
}
project_vars = {
    "project_id": "proj-123",
    "log_level": "DEBUG"  # Override app's log_level
}

varmgr.set_layer("app_defaults", app_vars)
varmgr.set_layer("project_env", project_vars)

# Get values from different scopes
app_log_level = varmgr.get_value("log_level", scope="scope_app")     # Returns "INFO"
proj_log_level = varmgr.get_value("log_level", scope="scope_project") # Returns "DEBUG"

# Get all values in a scope
project_values = varmgr.get_values(scope="scope_project")
# Returns merged values from project and app scopes
```

### Debugging and Inspection

```python
# Show available sources and their help text
varmgr.show_sources_help()

# Inspect variable resolution
var_info = varmgr.inspect_var("log_level", scope="scope_project")

# Get all source names for a scope
sources = varmgr.get_source_names(scope="scope_stack")
```

### Advanced Variable Usage

#### 1. Variable Combinations and Nesting

Variables can be combined and nested to create complex configurations:

```python
# Basic variable references
config = {
    "project_name": "myproject",
    "env": "prod",
    "stack_name": "${project_name}-${env}"  # Results in "myproject-prod"
}

# Nested references
config = {
    "base_name": "app",
    "version": "v1",
    "env": "prod",
    "name_with_version": "${base_name}-${version}",
    "full_name": "${name_with_version}-${env}"  # Results in "app-v1-prod"
}

# Multiple references to same variable
config = {
    "prefix": "svc",
    "double_prefix": "${prefix}-${prefix}",  # Results in "svc-svc"
    "with_suffix": "${prefix}-main-${prefix}"  # Results in "svc-main-svc"
}
```

#### 2. Special Characters and Edge Cases

The system handles various special characters and edge cases:

```python
config = {
    # Special characters are preserved
    "special_chars": "!@#$%^&*()",
    "with_special": "${special_chars}_suffix",  # Results in "!@#$%^&*()_suffix"
    
    # URLs and paths
    "url": "https://example.com",
    "path": "/path/to/file",
    "endpoint": "${url}${path}",  # Results in "https://example.com/path/to/file"
    
    # Whitespace handling
    "padded": "  ${url}  ",  # Preserves spaces: "  https://example.com  "
    
    # Unicode and emojis
    "unicode": "™®©",
    "emoji": "🌟🚀🎉",
    "combined": "${unicode}${emoji}"  # Results in "™®©🌟🚀🎉"
}
```

### Common Exceptions and Error Cases

#### 1. Circular References

The system detects and prevents circular variable references:

```python
# This will raise TemplateRenderingCircularValueError
config = {
    "var1": "${var2}",
    "var2": "${var1}"  # Circular reference!
}

# More complex circular reference with 4 variables
config = {
    "var1": "${var2}_a",
    "var2": "${var3}_b", 
    "var3": "${var4}_c",
    "var4": "${var1}_d"  # Creates circular reference var1 -> var2 -> var3 -> var4 -> var1
}
```

#### 2. Undefined Variables

Attempting to use undefined variables will raise an error:

```python
# This will raise UndefinedVarError
config = {
    "bad_ref": "${nonexistent_var}"  # Reference to undefined variable
}

# Using the error handler
varmgr.get_value("bad_ref", on_undefined_error="<UNDEFINED>")  # Returns "<UNDEFINED>"
```

#### 3. Malformed Templates

The system handles various malformed template cases:

```python
config = {
    # Missing closing brace - returned as-is
    "unclosed": "${var_without_closing",  # Returned unchanged
    
    # Invalid nested templates - processed as-is
    "invalid_nested": "${var${var}}",  # Returned unchanged
    
    # Extra closing braces - processed normally
    "extra_braces": "${var}}}",  # Extra braces preserved
    
    # Escaped dollar signs
    "escaped": "$$not_a_template",  # Double $ preserved
    "mixed": "$$literal_${var}_$$another"  # Combines escaped and template
}
```


