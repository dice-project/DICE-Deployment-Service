#!/usr/bin/env python

# This tool can be used for extracting configuration from TOSCA blueprints to be
# saved into files.
#
# Copyright 2016, XLAB d.o.o.

import sys
import argparse

from config_tool.utils import *

parser = argparse.ArgumentParser(
    description='Extract configuration from a TOSCA blueprint. It saves the '
    'extracted configuration into a file.')
group_mandatory = parser.add_argument_group('mandatory arguments')
group_mandatory.add_argument('-o', '--options',
        help='Configuration Optimization options file containing the '
        'config-to-parameter mappings')
group_mandatory.add_argument('-b', '--blueprint',
        help='The path to the blueprint file to be updated.')
group_mandatory.add_argument('-O', '--output',
        help='The path to the output, which will contain the extracted '
        'configuration.')

group_switches = parser.add_argument_group('switches')
group_switches.add_argument('--json', action='store_true',
        help='Configuration file is formatted as a JSON file.')
group_switches.add_argument('--matlab', action='store_true',
        help='Configuration file is formatted as a Matlab output file.')

args = parser.parse_args()

if not (args.options and args.blueprint and args.output):
    parser.print_help()
    sys.exit(1)

if args.json and args.matlab:
    print("Please provide only one of the following switches: "
            "--json or --matlab")
    sys.exit(1)

blueprint = load_blueprint(args.blueprint)
options = load_options(args.options)

configuration = extract_blueprint_config(blueprint, options)
if args.matlab:
    save_configuration_matlab(configuration, args.output)
else:
    save_configuration_json(configuration, args.output)
