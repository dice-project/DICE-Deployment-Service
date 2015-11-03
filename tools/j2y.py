#!/usr/bin/env python

import json
import yaml
import sys

try:
    in_data = open(sys.argv[1], "rb")
except:
    in_data = sys.stdin

data = json.load(in_data)
yaml.safe_dump(data, sys.stdout, default_flow_style = False)
