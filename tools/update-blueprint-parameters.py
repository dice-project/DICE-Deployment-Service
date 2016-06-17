#!/usr/bin/env python

# This tool can be used for updating the TOSCA blueprints with the parameter
# values loaded from a configuration file.
#
# Copyright 2016, XLAB d.o.o.

import sys
import argparse
import yaml

from config_tool.utils import *

parser = argparse.ArgumentParser(
    description='Update a TOSCA blueprint with new configuration values')
group_mandatory = parser.add_argument_group('mandatory arguments')
group_mandatory.add_argument('-o', '--options',
        help='Configuration Optimization options file containing the '
        'config-to-parameter mappings')
group_mandatory.add_argument('-c', '--configuration', 
        help='File containing the configuration values. Use --json (default) '
        'or --matlab to define the format.')
group_mandatory.add_argument('-b', '--blueprint',
        help='The path to the blueprint file to be updated.')
group_mandatory.add_argument('-O', '--output',
        help='The path to the updated blueprint output.')

group_switches = parser.add_argument_group('switches')
group_switches.add_argument('--json', action='store_true',
        help='Configuration file is formatted as a JSON file.')
group_switches.add_argument('--matlab', action='store_true',
        help='Configuration file is formatted as a Matlab output file.')

args = parser.parse_args()

if not (args.options and args.configuration and args.blueprint and \
        args.output):
    parser.print_help()
    sys.exit(1)

if args.json and args.matlab:
    print("Please provide only one of the following switches: "
            "--json or --matlab")
    sys.exit(1)

blueprint = load_blueprint(args.blueprint)
options = load_options(args.options)
if args.matlab:
    config = load_configuration_matlab(args.configuration)
else:
    config = load_configuration_json(args.configuration)

updated_blueprint = update_blueprint(blueprint, options, config)

with open(args.output, 'w') as f:
    yaml.safe_dump(updated_blueprint, f, default_flow_style = False)
