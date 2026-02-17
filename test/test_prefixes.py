import unittest

import ies_tool.ies_constants as ies_constants
import ies_tool.ies_tool as ies
from ies_tool.rdflib_plugin import RdfLibPlugin


class TestPrefixSetting(unittest.TestCase):

    def test_iestool_namespace_sets_default_prefix_on_init(self):
        """
        Verify that setting default_data_namespace on IESTool init
        automatically assigns this namespace to the default prefix (:).
        """
        custom_namespace = "http://test.example.com/mydata#"
        tool = ies.IESTool(default_data_namespace=custom_namespace)

        # Check that the ":" prefix is set to the custom namespace
        self.assertEqual(
            tool.prefixes[":"],
            custom_namespace,
            "The ':' prefix should be set to match default_data_namespace"
        )

    def test_iestool_namespace_prefix_updates_on_change(self):
        """
        When the namespace is changed after initialisation, the ":" prefix should
        automatically update to match.
        """
        tool = ies.IESTool()

        # Verify initial state
        self.assertEqual(tool.prefixes[":"], ies_constants.DEFAULT_DATA_NAMESPACE)

        # Change the namespace
        new_namespace = "http://changed.example.org/newdata#"
        tool.default_data_namespace = new_namespace

        # Verify the ":" prefix updated automatically
        self.assertEqual(
            tool.prefixes[":"],
            new_namespace,
            "The ':' prefix should automatically update when default_data_namespace changes"
        )

    def test_rdflib_plugin_prefix_updates_on_namespace_change(self):
        """
        Verify RdfLibPlugin updates ":" prefix when namespace changes.
        """
        plugin = RdfLibPlugin()
        new_namespace = "http://plugin.updated.org/data#"

        # Change the namespace
        plugin.default_data_namespace = new_namespace

        # Verify the ":" prefix was updated
        namespace_uri = plugin.get_namespace_uri(":")
        self.assertEqual(
            namespace_uri,
            new_namespace,
            "RdfLibPlugin should update ':' prefix when namespace is set"
        )

if __name__ == '__main__':
    unittest.main()
