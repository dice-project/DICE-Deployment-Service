#!/usr/bin/env python

from __future__ import print_function

import itertools
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
            desc = textwrap.fill(v.get("description", ""),
                                 initial_indent="| ", subsequent_indent="| ")
            if "default" not in v:
                print("+ {} [required]".format(k))
            else:
                print("+ {} [default: {}]".format(k, v["default"]))
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


class Graph(object):

    @staticmethod
    def add_subparser(subparsers, name, help):
        parser = subparsers.add_parser(name, help=help)
        parser.add_argument("-o", "--output", help="Output file",
                            type=argparse.FileType("w"), default="-")
        parser.add_argument("-c", "--color", action="store_true",
                            default=False,
                            help="Colorize output (DICE types are cyan)")
        parser.add_argument("-l", "--layout",
                            help="Output layout (graphviz's rankdir)",
                            default="TB",
                            choices=("TB", "LR", "BT", "RL"))
        return parser

    @staticmethod
    def write_head(layout, output):
        output.write("digraph {{\n"
                     "  node [shape=box style=filled fillcolor=white];\n"
                     "  edge [arrowhead=empty];\n"
                     "  rankdir={};\n\n".format(layout))

    @staticmethod
    def write_tail(output):
        output.write("\n}\n")

    @staticmethod
    def write_body(graph, output):
        for source, target in graph:
            output.write('  "{}" -> "{}";\n'.format(source, target))

    @staticmethod
    def write_nodes(graph, output):
        for node in set(itertools.chain(*graph)):
            color = "cyan2" if node.split(".", 1)[0] == "dice" else "white"
            output.write('  "{}" [fillcolor={}];\n'.format(node, color))
        output.write("\n")

    @staticmethod
    def write_graph(graph, output, color, layout):
        Graph.write_head(layout, output)
        if color:
            Graph.write_nodes(graph, output)
        Graph.write_body(graph, output)
        Graph.write_tail(output)


class NodeGraph(Command):

    @staticmethod
    def add_subparser(subparsers):
        return Graph.add_subparser(
            subparsers, "graph", "Prepare node dependency graph (dot format)"
        )

    def create_graph(self):
        return [(node["id"], rel["target_id"])
                for node in self.blueprint["nodes"]
                for rel in node["relationships"]]

    def execute(self, args):
        graph = self.create_graph()
        Graph.write_graph(graph, args.output, args.color, args.layout)


class TypeGraph(Command):

    @staticmethod
    def add_subparser(subparsers):
        return Graph.add_subparser(
            subparsers, "types", "Output type hierarchy graph (dot format)"
        )

    def create_graph(self):
        graph = {}
        for node in self.blueprint["nodes"]:
            type_hierarchy = node["type_hierarchy"][::-1]
            for typ, parent in zip(type_hierarchy, type_hierarchy[1:]):
                graph[typ] = parent
        return graph.items()

    def execute(self, args):
        graph = self.create_graph()
        Graph.write_graph(graph, args.output, args.color, args.layout)


class RelationshipGraph(Command):

    @staticmethod
    def add_subparser(subparsers):
        return Graph.add_subparser(
            subparsers, "relationships",
            "Output relationship hierarchy graph (dot format)"
        )

    def create_graph(self):
        graph = {}
        for node in self.blueprint["nodes"]:
            for rel in node["relationships"]:
                rel_hierarchy = rel["type_hierarchy"][::-1]
                for typ, parent in zip(rel_hierarchy, rel_hierarchy[1:]):
                    graph[typ] = parent
        return graph.items()

    def execute(self, args):
        graph = self.create_graph()
        Graph.write_graph(graph, args.output, args.color, args.layout)


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
