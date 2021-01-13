import argparse
import json
import sys
from pathlib import Path
from typing import Mapping
from shutil import rmtree
from itertools import islice

from openapi_type import parse_spec

from ..common.types import AttrStyle
from ..codegen import filegen


def is_empty_dir(p: Path) -> bool:
    return p.is_dir() and not bool(list(islice(p.iterdir(), 1)))


def setup(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    sub = subparsers.add_parser('gen', help='Generate client for a provided schema (JSON, YAML).')
    sub.add_argument('-s', '--source', help="Path to a spec (JSON, YAML). "
                                            "If not specified, then the data will be read from stdin.")
    sub.add_argument('-o', '--out-dir', required=True,
                     help="Output directory that will contain a newly generated Python client.")
    sub.add_argument('-qs', '--query-style',
                     required=False,
                     type=AttrStyle,
                     help="Style of query attributes: camelized, dasherized, unerscored. Default is dasherized.",
                     default=AttrStyle.DASHERIZED)
    sub.add_argument('-rs', '--request-style',
                     required=False,
                     type=AttrStyle,
                     help="Style of request attributes: camelized, dasherized, unerscored. Default is camelized.",
                     default=AttrStyle.CAMELIZED)
    sub.add_argument('-n', '--name', required=True,
                     help="Name of a newly generated Python client (package name).")
    sub.add_argument('-f', '--force-overwrite', required=False, action='store_true',
                     help="Overwrite existing files and directories if they already exist"
                     )
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

    layout = filegen.get_project_layout(
        spec=spec,
        root=Path(args.out_dir),
        name=args.name,
        query_style=args.query_style,
        request_style=args.request_style,
    )

    can_proceed = _overwrite_if_allowed_and_required(args, layout.root)
    if not can_proceed:
        return

    filegen.generate_from_layout(layout)

    out_channel.write('Done.\n')


def _overwrite_if_allowed_and_required(args: argparse.Namespace, root: Path) -> bool:
    can_proceed = True
    if root.exists() and not is_empty_dir(root):
        if args.force_overwrite:
            unlink = lambda: rmtree(str(root)) if root.is_dir() else root.unlink
            unlink()
        else:
            sys.stderr.write(f"Filepath already exists and is not empty: {str(root)}\n"
                             f"Use -f flag to explicitly allow overwriting it.\n")
            can_proceed = False
    return can_proceed


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
