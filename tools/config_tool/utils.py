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
    vars = load_yaml(options_file_path)['vars']
    return [{'paramname': v['paramname'], 'node': v['node']} for v in vars]


def load_configuration_matlab(configuration_file_path):
    """
    Loads a matlab text dump of the configuration numerical values
    and stores them in a Python array.
    """
    config = []
    with open(configuration_file_path, 'r') as f:
        for line in f.readlines():
            if line.strip().lower() == 'nan':
                v = None
            else:
                v = float(line)
                if v.is_integer():
                    v = int(v)
            config.append(v)

    return config


def save_configuration_matlab(configuration, file_path):
    """
    Saves a configuration represented by a Python array into a file containing a
    matlab-like output.
    """
    with open(file_path, 'w') as f:
        for v in configuration:
            v = 'NaN' if v == None else v
            f.write("    {0}\n".format(v))


def load_configuration_json(configuration_file_path):
    """
    Loads a json representation of the configuration and stores it in
    a Python array.
    """
    with open(configuration_file_path, 'r') as f:
        data = json.load(f)

    return data['config']


def save_configuration_json(configuration, file_path):
    """
    Saves a configuration represented by a Python array into a json file.
    """
    config_dict = {'config': configuration}
    with open(file_path, 'w') as f:
        json.dump(config_dict, f)


def set_configuration_value(node, paramname, value):
    props = node.get('properties', {})
    conf = props.get('configuration', {})
    conf[paramname] = value
    props['configuration'] = conf
    node['properties'] = props


def update_blueprint(input_blueprint, options, config):
    """
    Updates the input TOSCA blueprint with the new configuration values and
    produces an updated TOSCA blueprint.

    `input_blueprint`: the blueprint to update
    `options`: a dictionary with the Configuration Optimization options
    `config`: the configuration values to be updated.
    """
    updated_blueprint = copy.deepcopy(input_blueprint)

    assert(len(options) == len(config))

    for option, value in zip(options, config):
        paramname = option['paramname']
        nodes = option['node']
        nodes = [nodes] if isinstance(nodes, basestring) else nodes
        for node in nodes:
            node_template = updated_blueprint['node_templates'][node]
            if value != None:
                set_configuration_value(node_template, paramname, value)
            else:
                if paramname in node_template:
                    del node_template[paramname]

    return updated_blueprint

def extract_blueprint_config(blueprint, options):
    """
    Extracts the properties from the TOSCA blueprint to create a configuration
    values array.
    """
    config = [ ]
    node_templates = blueprint.get('node_templates', {})

    for option in options:
        node_names = option['node']
        node_names = [node_names] if isinstance(node_names, basestring) \
            else node_names
        cfg_vals = set()
        for node_name in node_names:
            node = node_templates.get(node_name, {})
            properties = node.get('properties', {})
            configuration = properties.get('configuration', {})
            parameter = configuration.get(option['paramname'], None)
            cfg_vals.add(parameter)

        cfg_vals = cfg_vals - set([None])
        if len(cfg_vals) > 1:
            raise Exception("Conflict in nodes {0}, parameter {1}.".format(
                node_names, option['paramname']))
        elif len(cfg_vals) == 1:
            config.append(cfg_vals.pop())
        else:
            config.append(None)

    return config
