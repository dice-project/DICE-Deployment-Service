import copy
import yaml
import json


def load_yaml(yaml_file_path):
    """Loads a YAML file"""
    with open(yaml_file_path, 'r') as f:
        data = yaml.load(f)

    return data


def load_blueprint(blueprint_file_path):
    """Loads a TOSCA YAML blueprint"""
    return load_yaml(blueprint_file_path)


def load_options(options_file_path):
    """Loads a Configuration optimization YAML file"""
    options_raw = load_yaml(options_file_path)
    options = [ ]

    nvars = len(options_raw) - 1

    for i in range(nvars):
        key = 'var%d' % (i + 1)
        item = {
            'paramname': options_raw[key]['paramname'],
            'node': options_raw[key]['node']
        }
        options += [ item ]

    return options


def load_configuration_matlab(configuration_file_path):
    """
    Loads a matlab text dump of the configuration numerical values
    and stores them in a Python array.
    """
    config = [ ]
    with open(configuration_file_path, 'r') as f:
        for line in f.readlines():
            v = float(line)
            if v.is_integer():
                v = int(v)
            config += [ v ]

    return config


def load_configuration_json(configuration_file_path):
    """
    Loads a json representation of the configuration and stores it in 
    a Python array.
    """
    with open(configuration_file_path, 'r') as f:
        data = json.load(f)

    return data['config']


def update_blueprint(input_blueprint, options, config):
    """
    Updates the input TOSCA blueprint with the new configuration values and
    produces an updated TOSCA blueprint.

    `input_blueprint`: the blueprint to update
    `options`: a dictionary with the Configuration Optimization options
    `config`: the configuration values to be updated.
    """
    import types

    updated_blueprint = copy.deepcopy(input_blueprint)

    assert(len(options) == len(config))

    for i in range(len(options)):
        paramname = options[i]['paramname']
        nodes = options[i]['node']
        if isinstance(nodes, types.StringTypes):
            nodes = [ nodes ]

        for node in nodes:
            node_template = updated_blueprint['node_templates'][node]
            node_properties = node_template.get('properties', { })
            node_properties[paramname] = config[i]
            if not 'properties' in node_template:
                node_template['properties'] = node_properties

    return updated_blueprint
