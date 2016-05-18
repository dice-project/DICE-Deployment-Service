import unittest
import copy
import os
import tempfile

from config_tool.utils import *

class TestConfigurationTransformation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(base_path, 'files')

        def fpath(*names):
            return os.path.join(file_path, *names)

        cls.blueprints = {
            'single-node': fpath('single-node-blueprint.yaml'),
            'full': fpath('full-blueprint.yaml'),
            'mixed': fpath('full-blueprint-mixed.yaml'),
            'conflicting': fpath('full-blueprint-conflicting.yaml'),
        }
        cls.options = {
            'normal': fpath('expconfig.yaml'),
            'multinode': fpath('expconfig-multinode.yaml'),
            'bad-var-info': fpath('expconfig-bad-var-info.yaml'),
        }
        cls.config = {
            'matlab': fpath('config-matlab.txt'),
            'json': fpath('config-matlab.json'),
        }


    def test_load_blueprint(self):
        """
        Load the blueprint from a yaml file and check its contents
        """
        blueprint = load_blueprint(self.blueprints['single-node'])
        self.assertIsNotNone(blueprint)

        self.assertTrue('tosca_definitions_version' in blueprint)
        self.assertTrue('imports' in blueprint)
        self.assertTrue('node_templates' in blueprint)
        self.assertTrue('outputs' in blueprint)

        node_templates = blueprint['node_templates']
        self.assertTrue('storm_vm' in node_templates)
        self.assertTrue('storm' in node_templates)

        storm = node_templates['storm']
        self.assertTrue('properties' in storm)

        storm_config = storm['properties']['configuration']
        expected_storm_config = {
                "component.count_bolt_num": 1,
                "component.split_bolt_num": 1,
                "component.spout_num": 3,
                "storm.messaging.netty.min_wait_ms": 100,
                "topology.max.spout.pending": 100,
                "topology.sleep.spout.wait.strategy.time.ms": 1
            }
        self.assertEqual(expected_storm_config, storm_config)

    def test_load_options(self):
        """
        Load the Configuration Optimization options and check their
        contents.
        """
        options = load_options(self.options['normal'])

        expected_options = [
            { 'node': 'storm', 'paramname': 'component.spout_num' },
            { 'node': 'storm', 'paramname': 'topology.max.spout.pending' },
            { 'node': 'storm', 
                'paramname': 'topology.sleep.spout.wait.strategy.time.ms' },
            { 'node': 'storm', 'paramname': 'component.split_bolt_num' },
            { 'node': 'storm', 'paramname': 'component.count_bolt_num' },
            { 'node': 'storm', 
                'paramname': 'storm.messaging.netty.min_wait_ms' },
        ]

        self.assertEqual(expected_options, options)

    def test_load_options_multiple_nodes(self):
        """
        Load the Configuration Optimization options containing several nodes
        and check their contents.
        """
        options = load_options(self.options['multinode'])

        expected_options = [
            {
                'node': ['storm', 'storm_nimbus'],
                'paramname': 'component.spout_num'
            },
            {
                'node': ['storm', 'storm_nimbus'],
                'paramname': 'topology.max.spout.pending'
            },
            {
                'node': ['storm', 'storm_nimbus'],
                'paramname': 'topology.sleep.spout.wait.strategy.time.ms'
            },
            {
                'node': ['storm', 'storm_nimbus'],
                'paramname': 'component.split_bolt_num'
            },
            {
                'node': ['storm', 'storm_nimbus'],
                'paramname': 'component.count_bolt_num'
            },
            {
                'node': ['storm', 'storm_nimbus'],
                'paramname': 'storm.messaging.netty.min_wait_ms'
            },
            {
                'node': 'zookeeper',
                'paramname': 'tickTime'
            },
            {
                'node': 'zookeeper',
                'paramname': 'initLimit'
            },
            {
                'node': 'zookeeper',
                'paramname': 'syncLimit'
            },
        ]

        self.assertEqual(expected_options, options)

    def test_load_options_bad_var_info(self):
        """
        Loading of variables where not all fields are present is not supported
        """
        with self.assertRaises(KeyError):
            load_options(self.options['bad-var-info'])

    def test_load_config_matlab(self):
        """
        Test loading the configuration data. We assume that this is a dump
        from Matlab.
        """
        expected_config = [2, 4, 10, 15000, 20, 2.400003]
        config = load_configuration_matlab(self.config['matlab'])

        self.assertEqual(expected_config, config)

    def test_load_config_json(self):
        """
        Test loading the configuration data. We assume that this is a json file
        containing an array.
        """
        expected_config = [2, 4, 10, 15000, 20, 2.400003]
        config = load_configuration_json(self.config['json'])

        self.assertEqual(expected_config, config)

    def test_export_config(self):
        """
        Confirm that the configuration values exported to string (for text file
        outputs) can be read back again properly.
        """
        # example configurations
        configurations = [
            [ 3, 100, 1, 2, 3, 110 ],
            [ 3, 100, None, 2, 3, 110, None ],
            [ ],
        ]

        for configuration in configurations:
            with tempfile.NamedTemporaryFile('w+') as f:
                fname = f.name
                # dump json
                save_configuration_json(configuration,
                    fname)
                # read json back
                configuration_imported_json = load_configuration_json(fname)
                # check the contents
                self.assertEqual(configuration, configuration_imported_json)
                # dump matlab
                save_configuration_matlab(configuration, fname)
                # read matlab back
                configuration_imported_matlab = load_configuration_matlab(fname)
                # check the contents
                self.assertEqual(configuration, configuration_imported_matlab)

    def test_single_node_update(self):
        """
        Load a blueprint with a single node (one VM, one Storm service
        on top of it). Update the blueprint with new configurations.
        """
        # Load and set the input parameters
        blueprint = load_blueprint(self.blueprints['single-node'])
        options = load_options(self.options['normal'])
        config = [ 2, 4, 10, 15, 20, 2 ]

        # routine check of the blueprint representation
        self.assertIsNotNone(blueprint)
        self.assertTrue('node_templates' in blueprint)

        node_templates = blueprint['node_templates']
        self.assertTrue('storm' in node_templates)

        # run the update
        updated_blueprint = update_blueprint(blueprint, options, config)

        # prepare the expected values
        configuration = {
                "component.spout_num": 2,
                "topology.max.spout.pending": 4,
                "topology.sleep.spout.wait.strategy.time.ms": 10,
                "component.split_bolt_num": 15,
                "component.count_bolt_num": 20,
                "storm.messaging.netty.min_wait_ms": 2
            }
        blueprint['node_templates']['storm']['properties']['configuration'] = \
            configuration

        # verify the outcome
        self.maxDiff = None
        self.assertEqual(blueprint, updated_blueprint)

    def test_single_node_shorter_config(self):
        """
        Test updating a blueprint where the blueprint has a longer list of
        properties than the configuration to be updated.
        """
        # Load and set the input parameters: truncated options and config values
        blueprint = load_blueprint(self.blueprints['single-node'])
        options = load_options(self.options['normal'])
        options = options[0:4]
        config = [ 2, 4, 10, 15 ]
        self.assertEqual(len(config), len(options))

        # routine check of the blueprint representation
        self.assertIsNotNone(blueprint)
        self.assertTrue('node_templates' in blueprint)

        node_templates = blueprint['node_templates']
        self.assertTrue('storm' in node_templates)

        # run the update
        updated_blueprint = update_blueprint(blueprint, options, config)

        # prepare the expected values
        configuration = {
                "component.spout_num": 2,
                "topology.max.spout.pending": 4,
                "topology.sleep.spout.wait.strategy.time.ms": 10,
                "component.split_bolt_num": 15,
                "component.count_bolt_num": 1,
                "storm.messaging.netty.min_wait_ms": 100
            }
        blueprint['node_templates']['storm']['properties']['configuration'] = \
            configuration

        # verify the outcome
        self.assertEqual(blueprint, updated_blueprint)

    def test_single_node_longer_config(self):
        """
        Test updating a blueprint where the configuration to be updated has a
        longer list of properties than the configuration to be updated.
        """
        # Load and set the input parameters
        blueprint = load_blueprint(self.blueprints['single-node'])
        options = load_options(self.options['normal'])
        config = [ 2, 4, 10, 15, 20, 2 ]

        # routine check of the blueprint representation
        self.assertIsNotNone(blueprint)
        self.assertTrue('node_templates' in blueprint)

        node_templates = blueprint['node_templates']
        self.assertTrue('storm' in node_templates)

        # truncate the blueprint's parameter list
        blueprint_storm_config = \
            blueprint['node_templates']['storm']['properties']['configuration']
        del blueprint_storm_config['component.split_bolt_num']
        del blueprint_storm_config['component.spout_num']
        del blueprint_storm_config['storm.messaging.netty.min_wait_ms']
        self.assertEqual(3, len(blueprint_storm_config))

        # run the update
        updated_blueprint = update_blueprint(blueprint, options, config)

        # prepare the expected values
        configuration = {
                "component.spout_num": 2,
                "topology.max.spout.pending": 4,
                "topology.sleep.spout.wait.strategy.time.ms": 10,
                "component.split_bolt_num": 15,
                "component.count_bolt_num": 20,
                "storm.messaging.netty.min_wait_ms": 2
            }
        blueprint['node_templates']['storm']['properties']['configuration'] = \
            configuration

        # verify the outcome
        self.maxDiff = None
        self.assertEqual(blueprint, updated_blueprint)

    def test_multiple_node_update(self):
        """
        Load a blueprint with multiple nodes. Update the blueprint with new
        configurations.
        """
        # Load and set the input parameters
        blueprint = load_blueprint(self.blueprints['full'])
        options = load_options(self.options['multinode'])
        config = [ 2, 4, 10, 15, 20, 2, 3000, 21, 7 ]

        # routine check of the blueprint representation
        self.assertIsNotNone(blueprint)
        self.assertTrue('node_templates' in blueprint)

        node_templates = blueprint['node_templates']
        self.assertTrue('storm' in node_templates)
        self.assertTrue('storm_nimbus' in node_templates)
        self.assertTrue('zookeeper' in node_templates)

        # run the update
        updated_blueprint = update_blueprint(blueprint, options, config)

        # prepare the expected values
        expected_storm_nimbus_config = {
                "component.spout_num": 2,
                "topology.max.spout.pending": 4,
                "topology.sleep.spout.wait.strategy.time.ms": 10,
                "component.split_bolt_num": 15,
                "component.count_bolt_num": 20,
                "storm.messaging.netty.min_wait_ms": 2
            }
        expected_storm_config = {
                "component.spout_num": 2,
                "topology.max.spout.pending": 4,
                "topology.sleep.spout.wait.strategy.time.ms": 10,
                "component.split_bolt_num": 15,
                "component.count_bolt_num": 20,
                "storm.messaging.netty.min_wait_ms": 2
            }
        expected_zookeeper_config = {
                "tickTime": 3000,
                "initLimit": 21,
                "syncLimit": 7
            }
        blueprint['node_templates']['storm']['properties']\
            ['configuration'] = expected_storm_config
        blueprint['node_templates']['storm_nimbus']['properties'] = \
            {'configuration': expected_storm_nimbus_config}
        blueprint['node_templates']['zookeeper']['properties']\
            ['configuration'] = expected_zookeeper_config

        # verify the outcome
        self.maxDiff = None
        self.assertEqual(blueprint, updated_blueprint)

    def test_multiple_node_partial_config_update(self):
        """
        In the input configuration, some of the values may be missing. In the
        Python array representation, the missing values are marked with None.
        The corresponding parameters then have to be absent from the blueprint
        (effectively setting them to the default value).
        """
        # Load and set the input parameters
        blueprint = load_blueprint(self.blueprints['mixed'])
        options = load_options(self.options['multinode'])
        config = [ None, 4, 10, 15, None, 2, 3000, 21, 7 ]

        # routine check of the blueprint representation
        self.assertIsNotNone(blueprint)
        self.assertTrue('node_templates' in blueprint)

        node_templates = blueprint['node_templates']
        self.assertTrue('storm' in node_templates)
        self.assertTrue('storm_nimbus' in node_templates)
        self.assertTrue('zookeeper' in node_templates)

        # run the update
        updated_blueprint = update_blueprint(blueprint, options, config)

        # prepare the expected values
        expected_storm_nimbus_config = {
               #"component.spout_num": 2, # omitted - missing in config
                "topology.max.spout.pending": 4,
                "topology.sleep.spout.wait.strategy.time.ms": 10,
                "component.split_bolt_num": 15,
                "component.spout_num": 3,
               #"component.count_bolt_num": 20,# missing in config and blueprint
                "storm.messaging.netty.min_wait_ms": 2,
                "nimbus.thrift.max_buffer_size": 1048576, # present in blueprint
            }
        expected_storm_config = {
               #"component.spout_num": 2, # omitted - missing in config
                "topology.max.spout.pending": 4,
                "topology.sleep.spout.wait.strategy.time.ms": 10,
                "component.split_bolt_num": 15,
                "component.spout_num": 3,
               #"component.count_bolt_num": 20,# missing in config and blueprint
                "storm.messaging.netty.min_wait_ms": 2,
                "nimbus.thrift.max_buffer_size": 1048576, # present in blueprint
            }
        expected_zookeeper_config = {
                "tickTime": 3000,
                "initLimit": 21,
                "syncLimit": 7,
                "preAllocSize": 64, # present in blueprint
            }
        blueprint['node_templates']['storm']['properties']\
            ['configuration'] = expected_storm_config
        blueprint['node_templates']['storm_nimbus']['properties'] = \
            {'configuration': expected_storm_nimbus_config}
        blueprint['node_templates']['zookeeper']['properties']\
            ['configuration'] = expected_zookeeper_config

        # verify the outcome
        self.maxDiff = None
        self.assertEqual(blueprint, updated_blueprint)


    def test_single_node_config_extract_full(self):
        """
        Load a blueprint with a single node (one VM, one Storm service
        on top of it). This blueprint has the complete set of propertes
        needed for the configuration.
        """
        # Load and set the input parameters
        blueprint = load_blueprint(self.blueprints['single-node'])
        options = load_options(self.options['normal'])

        # run the extraction
        extracted_config = extract_blueprint_config(blueprint, options)

        # prepare the expected values
        config = [ 3, 100, 1, 1, 1, 100 ]

        # verify the outcome
        self.assertEqual(config, extracted_config)

    def test_multiple_node_config_extract_full(self):
        """
        Load a blueprint with multiple nodes, which already has the set of
        properties matching the ones in the configuration.
        """
        # Load and set the input parameters
        blueprint = load_blueprint(self.blueprints['full'])
        options = load_options(self.options['multinode'])

        # run the extraction
        extracted_config = extract_blueprint_config(blueprint, options)

        # prepare the expected values
        config = [ 3, 100, 1, 1, 1, 100, 1500, 10, 5 ]

        # verify the outcome
        self.assertEqual(config, extracted_config)

    def test_multiple_node_config_extract_mixed(self):
        """
        Load a blueprint with multiple nodes, which has a mixed set of
        properties in comparison with the options: some of the properties are
        present, some are missing, and there are a few in the blueprint that are
        not declared in the options. The extraction needs to pick up the ones
        that are present, use a dedicated value for the missing ones and ignore
        the extra ones in the blueprint.
        """
        # Load and set the input parameters
        blueprint = load_blueprint(self.blueprints['mixed'])
        options = load_options(self.options['multinode'])

        # run the extraction
        extracted_config = extract_blueprint_config(blueprint, options)

        # prepare the expected values
        config = [ 3, 100, 1, None, None, 100, None, 10, 5 ]

        # verify the outcome
        self.assertEqual(config, extracted_config)

    def test_multiple_node_config_extract_conflicting(self):
        """
        Load a blueprint with multiple nodes, which already has the set of
        properties matching the ones in the configuration. The properties
        appearing in multiple nodes have conflicting values, which the
        tool has to reject with an error.
        """

        # Load and set the input parameters
        blueprint = load_blueprint(self.blueprints['conflicting'])
        options = load_options(self.options['multinode'])

        # run the extraction
        with self.assertRaises(Exception):
            extracted_config = extract_blueprint_config(blueprint, options)


if __name__ == '__main__':
    unittest.main()
