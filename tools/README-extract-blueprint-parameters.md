Blueprint configuration extractor tool
======================================

Introduction
------------

This tool complements the [blueprint updater tool].
It creates a configuration file containing the values of the parameters
in the blueprint as expressed in the options file.

Usage example
-------------

To use the tool, we need the following input:

* A valid TOSCA blueprint, e.g., `blueprint.yaml`.
* An options file, e.g., `expconfig.yaml`, which declares the variables
  in the configuration file, each associated with a name of a parameter
  and a node name in the blueprint.

To save the configuration values of the node templates in the blueprint into a
JSON file named `config.json`, we invoke:

```bash
$ ./extract_blueprint_parameters.py \
    --options expconfig.yaml \
    --blueprint blueprint.yaml \
    --json \
    --output config.json
```

Use `--matlab` instead of `--json` and `config.mat` as the value of the
`--output` option to use the alternative output format.

Input file specification
------------------------

The input files follow the same rules as for the [blueprint updater tool].

**Configuration file** will contain the values that the tool finds in the
blueprint's node template preferences in the order defined in the options file.
For the parameters appearing in multiple nodes (i.e., the ones where the
value corresponding to the `node` key is an array of names), the following
rules apply:

* All the node templates listed in the array by name have to have the same value
  of the parameter. If values differ, the tool will stop with an error.
* If some of the node templates listed in the array have a value while in other
  node templates the parameter is missing, the value from the node templates
  that have the parameter defined will appear in the configuration file. For
  those node templates, the same rule applies as the one in the previous bullet.
* If none of the node templates listed in the array are missing the parameter,
  then the corresponding configuration value will be `null` in the JSON output
  and `NaN` in the Matlab output.

[blueprint updater tool]: tools/README-update-blueprint-parameters.md