#!/usr/bin/env python

import sys
import json
import argparse

class ArgParser(argparse.ArgumentParser):
    """
    Argument parser that displays help on error
    """

    def error(self, message):
        sys.stderr.write("error: {}\n".format(message))
        self.print_help()
        sys.exit(2)


def make_dict(inputsfile):
    try:
        inputs = json.load(inputsfile)
    except Exception as e:
        print("Error reading {}: {}".format(inputsfile.name, e))
        sys.exit(1)
    return { entry['key']: entry for entry in inputs }


def make_outputs(inputdict):
    return list(inputdict.values())


def main(newinputs, oldinputs, output):
    basedict = make_dict(oldinputs)
    newdict  = make_dict(newinputs)

    basedict.update(newdict)

    outputdata = make_outputs(basedict)

    json.dump(outputdata, output, indent=2)


if __name__ == "__main__":
    parser = ArgParser(description="Update and extend contents of JSON")
    parser.add_argument("newinputs", help="JSON file containing new values",
                        type=argparse.FileType("r"))
    parser.add_argument("oldinputs", help="JSON file containing existing values",
                        type=argparse.FileType("r"))
    parser.add_argument("output", help="Output JSON file",
                        type=argparse.FileType("w"))
    args = parser.parse_args()

    main(args.newinputs, args.oldinputs, args.output)
