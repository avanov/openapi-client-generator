import argparse
import sys

from pkg_resources import get_distribution

from . import gen


NAME = "openapi-client-generator"

def main(args=None, in_channel=sys.stdin, out_channel=sys.stdout):
    parser = argparse.ArgumentParser(description='OpenAPI Client Generator')
    parser.add_argument('-V', '--version', action='version',
                        version=f'{NAME} {get_distribution(NAME).version}')
    subparsers = parser.add_subparsers(title='sub-commands',
                                       description='valid sub-commands',
                                       help='additional help',
                                       dest='sub-command')
    # make subparsers required (see http://stackoverflow.com/a/23354355/458106)
    subparsers.required = True

    # $ <cmd> gen
    # ---------------------------
    gen.setup(subparsers)

    # Parse arguments and config
    # --------------------------
    if args is None:
        args = sys.argv[1:]
    args = parser.parse_args(args)

    # Set up and run
    # --------------
    args.run_cmd(args, in_channel=in_channel, out_channel=out_channel)
