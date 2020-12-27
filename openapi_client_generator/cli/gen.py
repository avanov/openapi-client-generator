import argparse
import json
import sys
from pathlib import Path
from typing import Dict


def setup(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    sub = subparsers.add_parser('gen', help='Generate client for a provided schema (JSON, YAML)')
    sub.add_argument('-s', '--source', help="Path to a spec (JSON, YAML). "
                                            "If not specified, then the data will be read from stdin.")
    sub.set_defaults(func=main)
    return sub


def main(args: argparse.Namespace, out_channel=sys.stdout) -> None:
    """ $ <cmd-prefix> gen <source> <target>
    """
    try:
        with Path(args.source).open('r') as f:
            python_data = _read_data(f)
    except TypeError:
        # source is None, read from stdin
        python_data = _read_data(sys.stdin)

    out_channel.write(python_data)
    out_channel.write('\n')


def _read_data(fd) -> Dict:
    buf = fd.read()  # because stdin does not support seek
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
