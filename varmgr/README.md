# Variable Manager (varmgr)

Hierarchical configuration management with scoping, layering, and optional shell-style template resolution.


## Table of Contents

- [Goal](#goal)
- [Technical Implementation Overview](#technical-implementation-overview)
    - [Core Concepts](#core-concepts)
    - [1. Sources](#1-sources)
    - [2. Scopes](#2-scopes)
    - [3. Variable Resolution](#3-variable-resolution)
- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [Basic Usage](#basic-usage)
- [Template Variables](#template-variables)
- [Working with Multiple Scopes](#working-with-multiple-scopes)
- [Debugging and Inspection](#debugging-and-inspection)
- [Advanced Variable Usage](#advanced-variable-usage)
- [Common Exceptions and Error Cases](#common-exceptions-and-error-cases)


## Goal

varmgr manages configuration variables across scopes and layers:

- Scopes with inheritance (application → project → stack)
- Predictable overrides and fallbacks by source priority
- Optional recursive template resolution (`${var}` / `$var`)
- Multiple sources (CLI, environment, config files, defaults, …)


## Requirements

* Python 3.11+
* [expandvars](https://github.com/mrjk/python-expandvars) fork (`develop` branch) for template rendering:

```bash
pip install git+https://github.com/mrjk/python-expandvars.git@develop
```


## Technical Implementation Overview

### Core Concepts

#### 1. Sources

Sources are named config origins with an optional priority `level` (lower = higher priority).

```python
Source("app_cli", level=300, help="Application main CLI")
Source("app_env", level=300, help="Application environment variables")
Source("app_defaults", level=999, help="Application defaults")
```

#### 2. Scopes

Scopes list sources (and other scopes) to resolve against. Typical layout:

- `scope_app` — application sources
- `scope_project` — project sources, then inherit `scope_app`
- `scope_stack` — stack sources, then inherit `scope_project`

#### 3. Variable Resolution

Two APIs:

1. **`StoreManager`** — raw storage: `get_value` / `get_values` return stored values as-is (templates are **not** expanded).
2. **`RenderableStoreManager`** — same raw API, plus `get_renderer(scope).render_var(...)` / `render_values(...)` for expansion.


## Quickstart

### Basic Usage

```python
from lib.store import StoreManager, Source

varmgr = StoreManager()

varmgr.add_sources([
    Source("app_cli", level=300, help="Application main CLI"),
    Source("app_env", level=300, help="Application environment variables"),
    Source("app_defaults", level=999, help="Application defaults"),
])

varmgr.set_scopes({
    "scope_app": ["app_cli", "app_env", "app_defaults"],
    "scope_project": [
        "project_cli",
        "project_env",
        "project_defaults",
        "scope_app",
    ],
})

varmgr.set_layer("app_cli", {
    "app_name": "myapp",
    "debug": True,
})

app_name = varmgr.get_value("app_name")  # "myapp"
```

### Template Variables

`get_value` always returns the **raw** stored value. Use a `Renderer` to expand templates.

```python
from lib.store import RenderableStoreManager, Source

varmgr = RenderableStoreManager()

# ... add_sources / set_scopes as above ...

varmgr.set_layer("project_env", {
    "project_name": "myproject",
    "env": "prod",
    "stack_name": "${project_name}-${env}",
})

# Raw (not expanded)
assert varmgr.get_value("stack_name") == "${project_name}-${env}"

# Rendered
renderer = varmgr.get_renderer(scope_name="scope_project")
assert renderer.render_var("stack_name") == "myproject-prod"

# Render all variables in a scope
values = renderer.render_values()
```

Default template engine is **expandvars** (shell-style `$VAR` / `${VAR}`). You can select the alternate Python `string.Template` engine:

```python
renderer = varmgr.get_renderer(scope_name="scope_project", engine="py_stringtemplate")
```

### Working with Multiple Scopes

```python
varmgr.set_layer("app_defaults", {
    "log_level": "INFO",
    "app_name": "myapp",
})
varmgr.set_layer("project_env", {
    "project_id": "proj-123",
    "log_level": "DEBUG",
})

# Raw lookups respect scope priority
varmgr.get_value("log_level", scope="scope_app")      # "INFO"
varmgr.get_value("log_level", scope="scope_project")  # "DEBUG"

# Merged raw values for a scope (templates not expanded)
project_values = varmgr.get_values(scope="scope_project")
```

### Debugging and Inspection

```python
varmgr.show_sources_help()

# Layers that define a variable, highest priority first
layers = varmgr.inspect_var("log_level", scope="scope_project")

sources = varmgr.get_source_names(scope="scope_stack")

# Render with debug metadata
value, report = renderer.render_var("stack_name", debug=True)
```

### Advanced Variable Usage

#### 1. Combinations and nesting

```python
config = {
    "project_name": "myproject",
    "env": "prod",
    "stack_name": "${project_name}-${env}",  # -> "myproject-prod"
}

config = {
    "base_name": "app",
    "version": "v1",
    "env": "prod",
    "name_with_version": "${base_name}-${version}",
    "full_name": "${name_with_version}-${env}",  # -> "app-v1-prod"
}
```

Expand with `renderer.render_var("full_name")` (not `get_value`).

#### 2. Special characters

```python
config = {
    "special_chars": "!@#$%^&*()",
    "with_special": "${special_chars}_suffix",
    "url": "https://example.com",
    "path": "/path/to/file",
    "endpoint": "${url}${path}",
}
```


## Common Exceptions and Error Cases

### 1. Circular References

```python
config = {
    "var1": "${var2}",
    "var2": "${var1}",
}

renderer = varmgr.get_renderer(scope_name="scope_stack")
# raises TemplateRenderingCircularValueError
renderer.render_var("var1")
```

### 2. Undefined Variables

```python
config = {
    "bad_ref": "${nonexistent_var}",
}

varmgr.set_layer("stack_env", config)
renderer = varmgr.get_renderer(scope_name="scope_stack")

# Default: raises UndefinedVarError
renderer.render_var("bad_ref")

# Custom handler via render_var settings
renderer.render_var("bad_ref", on_undefined_error="<UNDEFINED>")
```

### 3. Malformed Templates

Expandvars is generally lenient: unclosed braces and similar cases are often returned unchanged. Escaped dollars use `$$` (see tests for exact behavior with the fork).


## Running tests

From the `varmgr` directory (with expandvars develop available):

```bash
./run_tests.sh
# or
pytest tests/
```
