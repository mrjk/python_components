from pprint import pprint

from lib.store_base import Source, UndefinedVarError
from lib.store_template import RenderableStoreManager, TemplateRenderingCircularValueError


def main1():
    "Firs featureset"
    varmgr = RenderableStoreManager()


    varmgr.add_sources(
        [
            # App sources
            Source("app_cli", level=300, help="Application main CLI"),
            Source("app_env", level=300, help="Application environment variables"),
            Source("app_secret", level=300, help="Application secrets"),
            Source("app_config", level=400, help="Application configuration"),
            Source("app_defaults", level=999, help="Application defaults"),
            # Project sources
            Source("project_cli", level=300, help="Project main CLI"),
            Source("project_env", level=300, help="Project environment variables"),
            Source("project_secret", level=300, help="Project secrets"),
            Source("project_config", level=400, help="Project configuration"),
            Source("project_defaults", level=999, help="Project defaults"),
            # Stack sources
            Source("stack_defaults", level=999, help="Stack defaults"),
            Source("stack_cli", level=300, help="Stack main CLI"),
            Source("stack_env", level=300, help="Stack environment variables"),
            Source("stack_secret", level=999, help="Stack secrets"),
            Source("stack_config", level=999, help="Stack configuration"),
        ]
    )

    varmgr.set_scopes(
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
                # Defaults
                "scope_app",
            ],
            "scope_stack": [
                "stack_cli",
                "stack_env",
                "stack_defaults",
                # Defaults
                "scope_project",
            ],
        }
    )

    # pprint(out)
    # print("========================== Dumping OBJ:")
    # pprint (varmgr.__dict__)
    # print("========================== ")

    vars_1app_cli = {
        "app_name": "dataset1",
    }
    vars_1project_env = {
        "project_name": "project1",
        "project_name2": "project1+${stack_name}",
        "project_name3": "project1+${stack_name}__${stack_fname}",
        # This create a circular reference that raise an exception
        # this must be tested
        "project_name666": "project1+++${stack_fname666}",
    }
    vars_1stack_env = {
        "stack_name": "STACK_NAME",
        "stack_fname": "${project_name}_${stack_name}",
        "stack_fname666": "stack1+++${project_name666}",
        "stack_name_double": "${project_name}+++${project_name}",

        "fail_because_undefined": "${unexisting}",
    }


    varmgr.set_layer("app_cli", vars_1app_cli)
    varmgr.set_layer("project_env", vars_1project_env)
    varmgr.set_layer("stack_env", vars_1stack_env)
    print("========================== Dumping OBJ:")
    pprint(varmgr.__dict__)

    # Test scope_stack renderer

    renderer_app = varmgr.get_renderer("scope_app")
    # renderer_project = varmgr.get_renderer("scope_project")
    renderer_stack = varmgr.get_renderer("scope_stack")


    def test_values():

        # We ensure a var is present in a scope, and not in another one
        out = renderer_stack.render_var("stack_name")
        print("RESULT1:")
        print (out)
        assert out == "STACK_NAME"

        try:
            out = renderer_app.render_var("stack_name")
            assert False, "Exception should have been raised"
        except UndefinedVarError:
            pass


        # Then try the templating thing
        out = renderer_stack.render_var("stack_fname", template=False, cache=False)
        print("RESULT2:")
        print (out)
        assert out == "${project_name}_${stack_name}"


        out = renderer_stack.render_var("project_name2", template=False, cache=False)
        print("RESULT3:")
        print (out)
        assert out == "project1+${stack_name}"

        out = renderer_stack.render_var("project_name2", template=True, cache=False)
        print("RESULT4:")
        print (out)
        assert out == "project1+STACK_NAME"




        # print("\n\n\n\nRESULT5: - pre")
        out = renderer_stack.render_var("stack_fname", template=True, cache=False) #, debug=True)
        print("\n\nRESULT5:")
        pprint (out)
        # assert out == "${project_name}_${stack_name}"
        assert out == "project1_STACK_NAME"

        # print("================================================ FIX6")


        # print("\n\n\n\nRESULT6: - pre")
        out = renderer_stack.render_var("project_name3", template=False, cache=False) #, debug=True)
        print("\n\nRESULT6:")
        pprint (out)
        # assert out == "${project_name}_${stack_name}"
        assert out == "project1+${stack_name}__${stack_fname}"
        out = renderer_stack.render_var("project_name3", template=True, cache=False) #, debug=True)
        print("\n\nRESULT6:")
        pprint (out)
        # assert out == "${project_name}_${stack_name}"
        assert out == "project1+STACK_NAME__project1_STACK_NAME"




        # Test double times the same var call
        out = renderer_stack.render_var("stack_name_double", template=False, cache=False) #, debug=True)
        print("\n\nRESULT7:")
        pprint (out)
        # assert out == "${project_name}_${stack_name}"
        assert out == "${project_name}+++${project_name}"


        out = renderer_stack.render_var("stack_name_double", template=True, cache=False) #, debug=True)
        print("\n\nRESULT8:")
        pprint (out)
        # assert out == "${project_name}_${stack_name}"
        assert out == "project1+++project1"


        # print("================================================ FIX9")

        out = renderer_stack.render_var("project_name666", template=False, cache=False) #, debug=True)
        print("\n\nRESULT9:")
        pprint (out)
        # assert out == "${project_name}_${stack_name}"
        assert out == "project1+++${stack_fname666}"


        try:
            out = renderer_stack.render_var("project_name666", template=True, cache=False) #, debug=True)
            assert False, "Exception should have been raised"
        except TemplateRenderingCircularValueError:
            pass

        # print("\n\nRESULT10:")
        # pprint (out)
        # # assert out == "${project_name}_${stack_name}"
        # assert out == "project1+++project1_STACK_NAME"



        print("================================================ FIX10")

        # Try exception unexisting
        try:
            out = renderer_stack.render_var("fail_because_undefined2")
            assert False, "Exception should have been raised"
        except UndefinedVarError:
            pass

        out = renderer_stack.render_var("fail_because_undefined2", on_undefined_error="<UNDEFINED>")
        assert out == "<UNDEFINED>"

        # Try unexisting key in template
        try:
            out = renderer_stack.render_var("fail_because_undefined")
            assert False, "Exception should have been raised"
        except UndefinedVarError:
            pass


        out = renderer_stack.render_var("fail_because_undefined", on_undefined_error="<UNDEFINED>")
        print("\n\nRESULT10:")
        pprint (out)
        # assert out == "${project_name}_${stack_name}"
        assert out == "<UNDEFINED>"



        # out = renderer.render_values()
        # pprint(out)
        # expected = {
        #     "app_name": "dataset1",
        #     "project_name": "project1+STACK_NAME",
        #     "stack_fname": "project1+STACK_NAME_STACK_NAME",
        #     "stack_name": "STACK_NAME",
        # }
        # assert expected == out




    # def test_cache_debug():

    #     # Do not use cache and validate
    #     out1 = renderer.render_var("stack_fname", debug=True, cache=False)
    #     print("\nRESULT: stack_fname2")
    #     pprint(out1)

    #     # AI THIS TEST IS NOT COVERED BY UNIT TESTS
    #     out2 = renderer.render_var("stack_fname", debug=True, cache=False)
    #     print("\nRESULT: stack_fname2")
    #     # pprint(out1)
    #     pprint(out2)

    #     assert out1 == out2

    #     # Use cache and validate
    #     out1 = renderer.render_var("stack_fname", debug=True, cache=True)
    #     print("\nRESULT: stack_fname2")
    #     pprint(out1)

    #     out2 = renderer.render_var("stack_fname", debug=True, cache=True)
    #     print("\nRESULT: stack_fname2")
    #     pprint(out2)

    #     assert out1 != out2


    # test_cache_debug()
    # test_cache()
    test_values()

    print("Tests POC4 OK")


if __name__ == "__main__":
    main1()
