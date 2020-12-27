import io
import pytest
from openapi_client_generator.cli import main


@pytest.mark.parametrize('typ, input, output', [
    ('json', '{"data": "Hello"}', '{"data": "Hello"}\n'),
    ('yaml', 'data: Hello', '{"data": "Hello"}\n'),
])
def test_cli(typ, input, output):
    ins = io.StringIO(input)
    out = io.StringIO()
    main(args=["gen"], in_channel=ins, out_channel=out)
    out.seek(0)
    assert out.read() == output
