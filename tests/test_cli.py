import io
import pytest
import tempfile as tf
from openapi_client_generator.cli import main


@pytest.mark.parametrize('typ, input, output', [
    ('json', '{"data": "Hello"}', '{"data": "Hello"}\n'),
    ('yaml', 'data: Hello', '{"data": "Hello"}\n'),
])
def test_cli(typ, input, output):
    ins = io.StringIO(input)
    out = io.StringIO()
    with tf.TemporaryDirectory() as tempdir:
        main(args=["gen", "-o", tempdir, "-n", "test_client"], in_channel=ins, out_channel=out)
        out.seek(0)
        assert out.read() == output
