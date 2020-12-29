import argparse
import json
import sys
from pathlib import Path
from typing import Mapping

from openapi_type import parse_spec

from ..codegen.filegen import client_layout


def setup(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    sub = subparsers.add_parser('gen', help='Generate client for a provided schema (JSON, YAML).')
    sub.add_argument('-s', '--source', help="Path to a spec (JSON, YAML). "
                                            "If not specified, then the data will be read from stdin.")
    sub.add_argument('-o', '--out-dir', required=True,
                     help="Output directory that will contain a newly generated Python client.")
    sub.add_argument('-n', '--name', required=True,
                     help="Name of a newly generated Python client (package name).")
    sub.set_defaults(run_cmd=main)
    return sub


def main(args: argparse.Namespace, in_channel=sys.stdin, out_channel=sys.stdout) -> None:
    """ $ <cmd-prefix> gen <source> <target>
    """
    try:
        with Path(args.source).open('r') as f:
            python_data = _read_data(f)
    except TypeError:
        # source is None, read from stdin
        python_data = _read_data(in_channel)

    spec = parse_spec(python_data)

    layout = client_layout(spec, Path(args.out_dir), args.name)
    print(layout)

    json.dump(python_data, out_channel)
    out_channel.write('\n')


def _read_data(fd) -> Mapping:
    buf = fd.read()  # because stdin does not support seek and we want to try both json and yaml parsing
    try:
        struct = json.loads(buf)
    except ValueError:
        try:
            import yaml
        except ImportError:
            raise RuntimeError(
                "Could not parse data as JSON, and could not locate PyYAML library "
                "to try to parse the data as YAML. You can either install PyYAML as a separate "
                "dependency, or use the `third_party` extra tag:\n\n"
                "$ pip install openapi-client-generator[third_party]"
            )
        struct = yaml.full_load(buf)
    return struct
