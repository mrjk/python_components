import jsonschema
from jsonschema import Draft202012Validator, validators

# =====================================================================
# JSON Schema framework
# =====================================================================


def _extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for prop, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(prop, subschema["default"])

        for error in validate_properties(
            validator,
            properties,
            instance,
            schema,
        ):
            yield error

    return validators.extend(
        validator_class,
        {"properties": set_defaults},
    )


DefaultValidatingValidator = _extend_with_default(Draft202012Validator)


def json_validate_defaults(schema, payload):
    "Validate dict against schema and set defaults"
    DefaultValidatingValidator(schema).validate(payload)
    return payload


def json_validate(schema, payload):
    "Validate dict against schema"
    jsonschema.validate(payload, schema)
    return payload

