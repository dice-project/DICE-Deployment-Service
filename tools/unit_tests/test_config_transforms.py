import unittest
import copy

from config_tool.utils import *

class TestConfigurationTransformation(unittest.TestCase):

    FILE_PATH = 'unit_tests/files'

    FILE_SINGLE_NODE_BLUEPRINT = '%s/single-node-blueprint.yaml' % FILE_PATH

    FILE_CO_OPTIONS = '%s/expconfig.yaml' % FILE_PATH

    FILE_CONFIGURATION_MATLAB = '%s/config-matlab.txt' % FILE_PATH
    FILE_CONFIGURATION_JSON = '%s/config-matlab.json' % FILE_PATH

    def test_load_blueprint(self):
        """
        Load the blueprint from a yaml file and check its contents
        """
        blueprint = load_blueprint(self.FILE_SINGLE_NODE_BLUEPRINT)
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

        storm_properties = storm['properties']
        expected_storm_properties = {
                "component.count_bolt_num": 1,
                "component.split_bolt_num": 1,
                "component.spout_num": 3,
                "storm.messaging.netty.min_wait_ms": 100,
                "topology.max.spout.pending": 100,
                "topology.sleep.spout.wait.strategy.time.ms": 1
            }
        self.assertEqual(expected_storm_properties, storm_properties)

    def test_load_options(self):
        """
        Load the Configuration Optimization options and check their
        contents.
        """
        options = load_options(self.FILE_CO_OPTIONS)

        expected_options = [
            { 'paramname': 'component.spout_num' },
            { 'paramname': 'topology.max.spout.pending' },
            { 'paramname': 'topology.sleep.spout.wait.strategy.time.ms' },
            { 'paramname': 'component.split_bolt_num' },
            { 'paramname': 'component.count_bolt_num' },
            { 'paramname': 'storm.messaging.netty.min_wait_ms' },
        ]

        self.assertEqual(expected_options, options)

    def test_load_config_matlab(self):
        """
        Test loading the configuration data. We assume that this is a dump
        from Matlab.
        """
        expected_config = [2, 4, 10, 15000, 20, 2.400003]
        config = load_configuration_matlab(self.FILE_CONFIGURATION_MATLAB)

        self.assertEqual(expected_config, config)

    def test_load_config_json(self):
        """
        Test loading the configuration data. We assume that this is a json file
        containing an array.
        """
        expected_config = [2, 4, 10, 15000, 20, 2.400003]
        config = load_configuration_json(self.FILE_CONFIGURATION_JSON)

        self.assertEqual(expected_config, config)

    def test_single_node_update(self):
        """
        Load a blueprint with a single node (one VM, one Storm service
        on top of it). Update the blueprint with new configurations.
        """
        # Load and set the input parameters
        blueprint = load_blueprint(self.FILE_SINGLE_NODE_BLUEPRINT)
        options = load_options(self.FILE_CO_OPTIONS)
        config = [ 2, 4, 10, 15, 20, 2 ]

        # routine check of the blueprint representation
        self.assertIsNotNone(blueprint)
        self.assertTrue('node_templates' in blueprint)

        node_templates = blueprint['node_templates']
        self.assertTrue('storm' in node_templates)

        # prepare the expected values
        expected_blueprint = copy.deepcopy(blueprint)
        expected_storm_properties = {
                "component.spout_num": 2,
                "topology.max.spout.pending": 4,
                "topology.sleep.spout.wait.strategy.time.ms": 10,
                "component.split_bolt_num": 15,
                "component.count_bolt_num": 20,
                "storm.messaging.netty.min_wait_ms": 2
            }
        expected_blueprint['node_templates']['storm']['properties'] = \
            expected_storm_properties

        # run the update
        updated_blueprint = update_blueprint(blueprint, options, config)

        # verify the outcome
        self.maxDiff = None
        self.assertEqual(expected_blueprint, updated_blueprint)

    def test_single_node_shorter_config(self):
        """
        Test updating a blueprint where the blueprint has a longer list of
        properties than the configuration to be updated.
        """
        # Load and set the input parameters: truncated options and config values
        blueprint = load_blueprint(self.FILE_SINGLE_NODE_BLUEPRINT)
        options = load_options(self.FILE_CO_OPTIONS)
        options = options[0:4]
        config = [ 2, 4, 10, 15 ]
        self.assertEqual(len(config), len(options))

        # routine check of the blueprint representation
        self.assertIsNotNone(blueprint)
        self.assertTrue('node_templates' in blueprint)

        node_templates = blueprint['node_templates']
        self.assertTrue('storm' in node_templates)

        # prepare the expected values
        expected_blueprint = copy.deepcopy(blueprint)
        expected_storm_properties = {
                "component.spout_num": 2,
                "topology.max.spout.pending": 4,
                "topology.sleep.spout.wait.strategy.time.ms": 10,
                "component.split_bolt_num": 15,
                "component.count_bolt_num": 1,
                "storm.messaging.netty.min_wait_ms": 100
            }
        expected_blueprint['node_templates']['storm']['properties'] = \
            expected_storm_properties

        # run the update
        updated_blueprint = update_blueprint(blueprint, options, config)

        # verify the outcome
        self.assertEqual(expected_blueprint, updated_blueprint)

        # longer version of the verification - probably not needed
        #updated_storm_properties = \
        #    updated_blueprint['node_templates']['storm']['properties']
        #self.assertEqual(len(expected_storm_properties), \
        #    len(updated_storm_properties))
        #for k, v in expected_storm_properties.iteritems():
        #    self.assertEqual(v, updated_storm_properties[k],
        #        "Difference in %s (%s != %s)" % (k, v,
        #            updated_storm_properties[k]))


    def test_single_node_longer_config(self):
        """
        Test updating a blueprint where the configuration to be updated has a
        longer list of properties than the configuration to be updated.
        """
        # Load and set the input parameters
        blueprint = load_blueprint(self.FILE_SINGLE_NODE_BLUEPRINT)
        options = load_options(self.FILE_CO_OPTIONS)
        config = [ 2, 4, 10, 15, 20, 2 ]

        # routine check of the blueprint representation
        self.assertIsNotNone(blueprint)
        self.assertTrue('node_templates' in blueprint)

        node_templates = blueprint['node_templates']
        self.assertTrue('storm' in node_templates)

        # truncate the blueprint's parameter list
        blueprint_storm_properties = \
            blueprint['node_templates']['storm']['properties']
        del blueprint_storm_properties['component.split_bolt_num']
        del blueprint_storm_properties['component.spout_num']
        del blueprint_storm_properties['storm.messaging.netty.min_wait_ms']
        self.assertEqual(3,
            len(blueprint['node_templates']['storm']['properties']))

        # prepare the expected values
        expected_blueprint = copy.deepcopy(blueprint)
        expected_storm_properties = {
                "component.spout_num": 2,
                "topology.max.spout.pending": 4,
                "topology.sleep.spout.wait.strategy.time.ms": 10,
                "component.split_bolt_num": 15,
                "component.count_bolt_num": 20,
                "storm.messaging.netty.min_wait_ms": 2
            }
        expected_blueprint['node_templates']['storm']['properties'] = \
            expected_storm_properties

        # run the update
        updated_blueprint = update_blueprint(blueprint, options, config)

        # verify the outcome
        self.maxDiff = None
        self.assertEqual(expected_blueprint, updated_blueprint)

if __name__ == '__main__':
    unittest.main()
