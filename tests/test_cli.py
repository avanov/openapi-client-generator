""" These tests exist mostly for providing coverage report, as the same CLI functionality
is already tested outside pytest with `make example-clients`
"""
import io
import pytest
import tempfile as tf
from openapi_client_generator.cli import main
from .paths import SPECS


@pytest.mark.parametrize('name, spec_path', SPECS)
def test_cli(name, spec_path):
    out = io.StringIO()
    with tf.TemporaryDirectory() as tempdir:
        main(args=["gen", "-s", str(spec_path), "-o", tempdir, "-n", "test_client"], out_channel=out)
