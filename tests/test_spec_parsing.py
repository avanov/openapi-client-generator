import pytest as pt
from openapi_client_generator.oas_spec import serialize_spec, parse_spec, Specification
from .utils import load_spec
from .paths import SPECS


@pt.mark.parametrize('name, spec_file', SPECS)
def test_main(name, spec_file):
    try:
        s = load_spec(spec_file)
    except Exception as e:
        print(list(e))
        raise

    assert isinstance(s, Specification)
    assert parse_spec(serialize_spec(s)) == s
