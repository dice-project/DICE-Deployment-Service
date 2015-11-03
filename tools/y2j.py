#!/usr/bin/env python

import json
import yaml
import sys

try:
    in_data = open(sys.argv[1], "rb")
except:
    in_data = sys.stdin

data = yaml.safe_load(in_data)
json.dump(data, sys.stdout, indent = 2)
