import pytest

from lib.store_base import Source, UndefinedVarError
from lib.store_template import (
    RenderableStoreManager,
    TemplateRenderingCircularValueError,
)


@pytest.fixture
def varmgr():
    """Create a basic variable manager with predefined sources and scopes"""
    mgr = RenderableStoreManager()

    mgr.add_sources(
        [
            Source("app_cli", level=300, help="Application main CLI"),
            Source("app_env", level=300, help="Application environment variables"),
            Source("app_defaults", level=999, help="Application defaults"),
            Source("project_cli", level=300, help="Project main CLI"),
            Source("project_env", level=300, help="Project environment variables"),
            Source("project_defaults", level=999, help="Project defaults"),
            Source("stack_cli", level=300, help="Stack main CLI"),
            Source("stack_env", level=300, help="Stack environment variables"),
            Source("stack_defaults", level=999, help="Stack defaults"),
        ]
    )

    mgr.set_scopes(
        {
            "scope_app": [
                "app_cli",
                "app_env",
                "app_defaults",
            ],
            "scope_project": [
                "project_cli",
                "project_env",
                "project_defaults",
                "scope_app",
            ],
            "scope_stack": [
                "stack_cli",
                "stack_env",
                "stack_defaults",
                "scope_project",
            ],
        }
    )

    return mgr


def test_basic_variable_resolution(varmgr):
    """Test basic variable resolution without templates"""
    varmgr.set_layer("app_cli", {"app_name": "dataset1"})

    renderer = varmgr.get_renderer("scope_app")
    assert renderer.render_var("app_name") == "dataset1"


def test_get_value_is_raw_not_rendered(varmgr):
    """get_value returns stored templates; render_var expands them."""
    varmgr.set_layer(
        "project_env",
        {
            "project_name": "myproject",
            "env": "prod",
            "stack_name": "${project_name}-${env}",
        },
    )

    assert varmgr.get_value("stack_name") == "${project_name}-${env}"

    renderer = varmgr.get_renderer("scope_project")
    assert renderer.render_var("stack_name") == "myproject-prod"


def test_template_variable_resolution(varmgr):
    """Test resolving template variables with references"""
    varmgr.set_layer("app_cli", {"app_name": "dataset1"})
    varmgr.set_layer("project_env", {"project_name": "project1+${stack_name}"})
    varmgr.set_layer(
        "stack_env",
        {
            "stack_name": "dataset3",
            "stack_fname": "${project_name}_${stack_name}",
        },
    )

    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("app_name") == "dataset1"
    assert renderer.render_var("stack_name") == "dataset3"
    assert renderer.render_var("project_name") == "project1+dataset3"
    assert renderer.render_var("stack_fname") == "project1+dataset3_dataset3"


def test_template_caching(varmgr):
    """Test that template caching works correctly"""
    varmgr.set_layer("app_cli", {"app_name": "dataset1"})
    varmgr.set_layer("project_env", {"project_name": "project1+${stack_name}"})
    varmgr.set_layer(
        "stack_env",
        {
            "stack_name": "dataset3",
            "stack_fname": "${project_name}_${stack_name}",
        },
    )

    renderer = varmgr.get_renderer("scope_stack")

    result1 = renderer.render_var("stack_fname", cache=False)
    result2 = renderer.render_var("stack_fname", cache=False)
    assert result1 == result2

    result1 = renderer.render_var("stack_fname", cache=True)
    result2 = renderer.render_var("stack_fname", cache=True)
    assert result1 == result2


def test_debug_output(varmgr):
    """Test debug output format"""
    varmgr.set_layer("app_cli", {"app_name": "dataset1"})
    varmgr.set_layer("project_env", {"project_name": "project1+${stack_name}"})
    varmgr.set_layer(
        "stack_env",
        {
            "stack_name": "dataset3",
            "stack_fname": "${project_name}_${stack_name}",
        },
    )

    renderer = varmgr.get_renderer("scope_stack")
    value, debug_info = renderer.render_var("stack_fname", debug=True)

    assert value == "project1+dataset3_dataset3"
    assert debug_info["key"] == "stack_fname"
    assert "level" in debug_info
    assert "templated" in debug_info


def test_circular_reference_detection(varmgr):
    """Test detection of circular references"""
    varmgr.set_layer("project_env", {"project_name": "project1+${stack_fname}"})
    varmgr.set_layer("stack_env", {"stack_fname": "${project_name}_suffix"})

    renderer = varmgr.get_renderer("scope_stack")

    with pytest.raises(
        TemplateRenderingCircularValueError,
        match="Circular reference detected on 'stack_fname.*",
    ):
        renderer.render_var("stack_fname")


def test_undefined_variable(varmgr):
    """Test handling of undefined variables"""
    renderer = varmgr.get_renderer("scope_stack")

    with pytest.raises(UndefinedVarError):
        renderer.render_var("nonexistent_var")


def test_multiple_renderers(varmgr):
    """Test that multiple renderers for the same scope share the same instance"""
    renderer1 = varmgr.get_renderer("scope_stack")
    renderer2 = varmgr.get_renderer("scope_stack")

    assert renderer1 is renderer2


def test_non_template_values(varmgr):
    """Test handling of non-template values"""
    varmgr.set_layer(
        "stack_env",
        {
            "string_value": "simple string",
            "number_value": 42,
            "bool_value": True,
        },
    )
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("string_value") == "simple string"
    assert renderer.render_var("number_value") == 42
    assert renderer.render_var("bool_value") is True


def test_empty_template_string(varmgr):
    """Test handling of empty template strings"""
    varmgr.set_layer(
        "stack_env",
        {
            "empty_string": "",
            "template_with_spaces": "   ${other_var}   ",
            "other_var": "value",
        },
    )
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("empty_string") == ""
    assert renderer.render_var("template_with_spaces") == "   value   "


def test_nested_template_resolution(varmgr):
    """Test deeply nested template resolution"""
    varmgr.set_layer(
        "stack_env",
        {
            "var1": "one",
            "var2": "${var1}_two",
            "var3": "${var2}_three",
            "var4": "${var3}_four",
            "var5": "${var4}_five",
        },
    )
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("var5") == "one_two_three_four_five"


def test_special_characters_in_templates(varmgr):
    """Test handling of special characters in template strings"""
    varmgr.set_layer(
        "stack_env",
        {
            "special_chars": "!@#$%^&*()",
            "url": "https://example.com",
            "path": "/path/to/file",
            "template": "${special_chars}_${url}_${path}",
        },
    )
    renderer = varmgr.get_renderer("scope_stack")

    assert (
        renderer.render_var("template")
        == "!@#$%^&*()_https://example.com_/path/to/file"
    )


def test_multiple_references_same_var(varmgr):
    """Test multiple references to the same variable"""
    varmgr.set_layer(
        "stack_env",
        {
            "base": "value",
            "double_ref": "${base}_${base}",
            "triple_ref": "${base}_${base}_${base}",
        },
    )
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("double_ref") == "value_value"
    assert renderer.render_var("triple_ref") == "value_value_value"


def test_escaped_dollar_signs(varmgr):
    """Test handling of escaped dollar signs in templates"""
    varmgr.set_layer(
        "stack_env",
        {
            "var": "value",
            "unexisting": "$not_a_var",
            "escaped2": "$$not_a_template2",
            "escaped3": "$$$not_a_template3",
            "escaped4": "$$$$not_a_template4",
            "escaped5": "$$$$$not_a_template5",
            "escaped6": "$$$$$$not_a_template6",
            "escaped7": "$$$$$$$not_a_template7",
            "mixed": "$$literal_${var}_$$another",
        },
    )
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("escaped2") == "$$not_a_template2"
    assert renderer.render_var("escaped3") == "$$$not_a_template3"
    assert renderer.render_var("escaped4") == "$$$$not_a_template4"
    assert renderer.render_var("escaped5") == "$$$$$not_a_template5"
    assert renderer.render_var("escaped6") == "$$$$$$not_a_template6"
    assert renderer.render_var("escaped7") == "$$$$$$$not_a_template7"
    assert renderer.render_var("mixed") == "$$literal_value_$$another"


def test_scope_inheritance_with_templates(varmgr):
    """Test template resolution across different scopes with inheritance"""
    varmgr.set_layer("app_defaults", {"base_var": "app_value"})
    varmgr.set_layer("project_defaults", {"project_var": "${base_var}_project"})
    varmgr.set_layer("stack_defaults", {"stack_var": "${project_var}_stack"})

    app_renderer = varmgr.get_renderer("scope_app")
    project_renderer = varmgr.get_renderer("scope_project")
    stack_renderer = varmgr.get_renderer("scope_stack")

    assert app_renderer.render_var("base_var") == "app_value"
    assert project_renderer.render_var("project_var") == "app_value_project"
    assert stack_renderer.render_var("stack_var") == "app_value_project_stack"


def test_template_with_missing_closing_brace(varmgr):
    """Test handling of malformed templates with missing closing braces"""
    varmgr.set_layer(
        "stack_env",
        {
            "var": "value",
            "malformed": "${var_without_closing",
        },
    )
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("malformed") == "${var_without_closing"


def test_cache_invalidation_on_set_layer(varmgr):
    """set_layer clears renderer caches so later renders see new values."""
    varmgr.set_layer(
        "stack_env",
        {
            "base": "original",
            "dependent": "${base}_suffix",
        },
    )

    renderer = varmgr.get_renderer("scope_stack")
    assert renderer.render_var("dependent", cache=True) == "original_suffix"

    varmgr.set_layer(
        "stack_env",
        {
            "base": "modified",
            "dependent": "${base}_suffix",
        },
    )

    assert renderer.render_var("dependent", cache=True) == "modified_suffix"


def test_complex_nested_references(varmgr):
    """Test complex nested references with multiple variable types"""
    varmgr.set_layer(
        "stack_env",
        {
            "num": 42,
            "bool_val": True,
            "str_val": "string",
            "complex": "${str_val}_${num}_${bool_val}",
            "nested": "${complex}_${complex}",
        },
    )
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("complex") == "string_42_True"
    assert renderer.render_var("nested") == "string_42_True_string_42_True"


def test_template_substitution_edge_cases(varmgr):
    """Test various edge cases and special characters in template substitution"""
    vars_stack = {
        "special1": "!@#$%^&*()",
        "special2": "[]{}\\|;:'\",.<>/?",
        "special3": "~`",
        "special4": " \t\n\r",
        "special5": "™®©",
        "special6": "🌟🚀🎉",
        "dollar1": "$",
        "dollar2": "$$",
        "dollar3": "$$$",
        "dollar4": "${",
        "dollar5": "$}",
        "dollar6": "test'$'test",
        "dollar7": "$ {var}",
        "var": "base_value",
        "template1": "${var}${var}",
        "template2": "${var} ${var}",
        "template3": "$$${var}",
        "template4": "${var}$$",
        "template5": "$$${var}$$",
        "template6": "${special1}${special2}",
        "template7": "prefix${var}suffix",
        "template8": "  ${var}  ",
        "template9": "\t${var}\n",
        "template10": "${special5}${special6}",
        "nested1": "${template6}${template7}",
        "nested2": "${template8}${template9}",
        "problem1": "${var${var}}",
        "problem2": "${var}}}",
        "problem3": "${var{{}}",
        "problem4": "}{${var}}{",
        "problem5": "${not_existing}",
        "problem6": "${var_without_closing",
        "long1": "${var}" * 10,
        "long2": "$" * 50,
        "long3": "${" * 10,
        "long4": "}" * 10,
    }

    varmgr.set_layer("stack_env", vars_stack)
    renderer = varmgr.get_renderer("scope_stack")

    assert renderer.render_var("special1") == "!@#$%^&*()"
    assert renderer.render_var("special2") == "[]{}\\|;:'\",.<>/?"
    assert renderer.render_var("special3") == "~`"
    assert renderer.render_var("special4") == " \t\n\r"
    assert renderer.render_var("special5") == "™®©"
    assert renderer.render_var("special6") == "🌟🚀🎉"

    assert renderer.render_var("dollar1") == "$"
    assert renderer.render_var("dollar2") == "$$"
    assert renderer.render_var("dollar3") == "$$$"
    assert renderer.render_var("dollar4") == "${"
    assert renderer.render_var("dollar5") == "$}"
    assert renderer.render_var("dollar6") == "test'$'test"
    assert renderer.render_var("dollar7") == "$ {var}"

    assert renderer.render_var("template1") == "base_valuebase_value"
    assert renderer.render_var("template2") == "base_value base_value"
    assert renderer.render_var("template3") == "$$${var}"
    assert renderer.render_var("template4") == "base_value$$"
    assert renderer.render_var("template5") == "$$${var}$$"
    assert renderer.render_var("template6") == "!@#$%^&*()[]{}\\|;:'\",.<>/?"
    assert renderer.render_var("template7") == "prefixbase_valuesuffix"
    assert renderer.render_var("template8") == "  base_value  "
    assert renderer.render_var("template9") == "\tbase_value\n"
    assert renderer.render_var("template10") == "™®©🌟🚀🎉"

    assert (
        renderer.render_var("nested1")
        == "!@#$%^&*()[]{}\\|;:'\",.<>/?prefixbase_valuesuffix"
    )
    assert renderer.render_var("nested2") == "  base_value  \tbase_value\n"

    renderer.render_var("problem1")
    renderer.render_var("problem2")
    renderer.render_var("problem3")
    renderer.render_var("problem4")
    with pytest.raises(UndefinedVarError):
        renderer.render_var("problem5")
    renderer.render_var("problem6")

    assert renderer.render_var("long1") == "base_value" * 10
    assert renderer.render_var("long2") == "$" * 50
    assert renderer.render_var("long3") == "${" * 10
    assert renderer.render_var("long4") == "}" * 10


def test_template_debug_mode(varmgr):
    """Test template rendering in debug mode with special characters"""
    varmgr.set_layer(
        "stack_env",
        {
            "base": "value!@#$",
            "nested": "${base}_${base}",
            "complex": "prefix_${nested}_suffix",
        },
    )

    renderer = varmgr.get_renderer("scope_stack")

    value, debug_info = renderer.render_var("base", debug=True)
    assert value == "value!@#$"
    assert debug_info["key"] == "base"
    assert isinstance(debug_info["templated"], bool)

    value, debug_info = renderer.render_var("nested", debug=True)
    assert value == "value!@#$_value!@#$"
    assert debug_info["templated"]

    value, debug_info = renderer.render_var("complex", debug=True)
    assert value == "prefix_value!@#$_value!@#$_suffix"
    assert debug_info["templated"]
