#!/usr/bin/env python

from __future__ import print_function

import argparse
import textwrap
import inspect
import json
import yaml
import sys

from dsl_parser import parser as cfy_parser


class ArgParser(argparse.ArgumentParser):
    """
    Argument parser that displays help on error
    """

    def error(self, message):
        sys.stderr.write("error: {}\n".format(message))
        self.print_help()
        sys.exit(2)


class Command(object):

    def __init__(self, blueprint):
        self.blueprint = cfy_parser.parse_from_path(blueprint)


class Inputs(Command):

    @staticmethod
    def add_subparser(subparsers):
        parser = subparsers.add_parser("inputs", help="Inspect inputs")
        parser.add_argument("--format", help="Output format",
                            choices=["text", "dice", "cfy"], default="text")
        return parser

    @staticmethod
    def print_cfy(inputs):
        data = {k: v.get("default", "REPLACE_ME") for k, v in inputs.items()}
        print(yaml.safe_dump(data, default_flow_style=False))

    @staticmethod
    def print_dice(inputs):
        data = []
        for k, v in inputs.items():
            value = v.get("default", "REPLACE_ME")
            desc = v.get("description", "").strip()
            data.append(dict(key=k, value=value, description=desc))
        print(json.dumps(data, indent=2, sort_keys=True))

    @staticmethod
    def print_table(inputs):
        for k, v in sorted(inputs.items(), key=lambda x: x[0]):
            default = v.get("default", "")
            req = default == ""
            desc = textwrap.fill(v.get("description", ""),
                                 initial_indent="| ", subsequent_indent="| ")
            if req:
                print("+ {} [required]".format(k))
            else:
                print("+ {} [default: {}]".format(k, default))
            if desc != "":
                print(desc)
            print()

    def execute(self, args):
        inputs = self.blueprint.get("inputs", {})
        if len(self.blueprint.get("inputs", {})) == 0:
            return

        if args.format == "dice":
            self.print_dice(inputs)
        elif args.format == "cfy":
            self.print_cfy(inputs)
        elif args.format == "text":
            self.print_table(inputs)
        else:
            assert "Invalid format"


class Dump(Command):

    @staticmethod
    def add_subparser(subparsers):
        parser = subparsers.add_parser("dump", help="Dump processed blueprint")
        return parser

    def execute(self, args):
        print(json.dumps(self.blueprint, indent=2))


def create_parser():
    def is_command(item):
        return (inspect.isclass(item) and item != Command and
                issubclass(item, Command))

    parser = ArgParser(description="Blueprint data extractor")
    parser.add_argument("blueprint", help="Blueprint to inspect")
    subparsers = parser.add_subparsers()

    commands = inspect.getmembers(sys.modules[__name__], is_command)
    for _, cls in commands:
        sub = cls.add_subparser(subparsers)
        sub.set_defaults(cls=cls)

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    cmd = args.cls(args.blueprint)
    cmd.execute(args)


if __name__ == "__main__":
    main()
