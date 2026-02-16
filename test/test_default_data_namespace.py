import unittest

import ies_tool.ies_constants as ies_constants
import ies_tool.ies_tool as ies
from ies_tool.rdflib_plugin import RdfLibPlugin
from ies_tool.sparql_endpoint_plugin import SPARQLEndpointPlugin


class TestDefaultDataNamespace(unittest.TestCase):
    """
    Tests for default_data_namespace functionality across IESTool and plugin classes.
    """

    def test_default_namespace_constant_value(self):
        """
        Verify the DEFAULT_DATA_NAMESPACE constant is set correctly.
        The constant should be "http://example.com/rdf/testdata#" as documented in the README.
        """
        self.assertEqual(
            ies_constants.DEFAULT_DATA_NAMESPACE,
            "http://example.com/rdf/testdata#",
            "DEFAULT_DATA_NAMESPACE constant should match the documented default"
        )

    def test_iestool_default_namespace_when_mode_not_set(self):
        """
        When mode is not explicitly stated on init (defaults to "rdflib"),
        default_data_namespace should use the constant value.
        """
        tool = ies.IESTool()  # mode defaults to "rdflib"

        self.assertEqual(
            tool.default_data_namespace,
            ies_constants.DEFAULT_DATA_NAMESPACE,
            "IESTool should use DEFAULT_DATA_NAMESPACE constant when mode is not set"
        )


    def test_iestool_default_namespace_when_mode_set(self):
        """
        When mode is explicitly stated on init to "rdflib",
        default_data_namespace should use the constant value.
        """
        tool = ies.IESTool(mode="rdflib")

        self.assertEqual(
            tool.default_data_namespace,
            ies_constants.DEFAULT_DATA_NAMESPACE,
            "IESTool should use DEFAULT_DATA_NAMESPACE constant when mode is not set"
        )

    def test_iestool_namespace_set_when_mode_not_set(self):
        """
        When mode is not explicitly stated on init (defaults to "rdflib"),
        and a custom namespace is provided, it should be respected.
        """
        custom_namespace = "http://custom.example.org/data#"
        tool = ies.IESTool(default_data_namespace=custom_namespace)  # mode defaults to "rdflib"

        self.assertEqual(
            tool.default_data_namespace,
            custom_namespace,
            "IESTool should use custom namespace provided by user"
        )


    def test_iestool_namespace_set_when_mode_set(self):
        """
        When mode is explicitly stated on init to "rdflib",
        and a custom namespace is provided, it should be respected.
        """
        custom_namespace = "http://custom.example.org/data#"
        tool = ies.IESTool(mode="rdflib", default_data_namespace=custom_namespace)

        self.assertEqual(
            tool.default_data_namespace,
            custom_namespace,
            "IESTool should use custom namespace provided by user"
        )

    def test_iestool_namespace_set_with_plugin(self):
        """
        When a custom namespace is provided during initialisation alongside
        custom plugin, it should override the default value.
        """
        custom_namespace = "http://custom.example.org/data#"
        plugin = RdfLibPlugin()
        tool = ies.IESTool(mode=plugin, default_data_namespace=custom_namespace)

        self.assertEqual(
            tool.default_data_namespace,
            custom_namespace,
            "IESTool should use the user-provided namespace, not the default"
        )

    def test_iestool_namespace_set_with_one_set_in_plugin(self):
        """
        When a custom namespace is provided when init a custom plugin and
        one not set on init IESTool, then the one set in the plugin shall
        override the default value.
        """
        custom_namespace = "http://custom.example.org/data#"
        plugin = RdfLibPlugin(default_data_namespace=custom_namespace)
        tool = ies.IESTool(mode=plugin)

        self.assertEqual(
            tool.default_data_namespace,
            custom_namespace,
            "RdfLibPlugin should use the user-provided namespace, not the default"
        )

    def test_iestool_namespace_overrides_one_set_in_plugin(self):
        """
        When a custom namespace is provided in both the init of RdfLibPlugin
        and IESTool, the IESTool one prevails.
        """
        custom_namespace_1 = "http://custom.example.org/data1#"
        custom_namespace_2 = "http://custom.example.org/data2#"
        plugin = RdfLibPlugin(default_data_namespace=custom_namespace_1)
        tool = ies.IESTool(mode=plugin, default_data_namespace=custom_namespace_2)

        self.assertEqual(
            tool.default_data_namespace,
            custom_namespace_2,
            "IESTool should use its own namespace parameter, overriding the plugin's"
        )

    def test_rdflib_plugin_namespace_setter_works(self):
        """
        Verify RdfLibPlugin property setter works.
        """
        plugin = RdfLibPlugin()
        new_namespace = "http://updated.test.org/data#"

        # This should not raise NotImplementedError
        plugin.default_data_namespace = new_namespace

        self.assertEqual(
            plugin.default_data_namespace,
            new_namespace,
            "RdfLibPlugin should allow updating namespace via property setter"
        )

    def test_rdflib_plugin_namespace_getter_works(self):
        """
        Verify RdfLibPlugin property getter works.
        """
        new_namespace = "http://updated.test.org/data#"
        plugin = RdfLibPlugin(default_data_namespace=new_namespace)

        self.assertEqual(
            plugin.default_data_namespace,
            new_namespace,
            "RdfLibPlugin should return the namespace via property getter"
        )


    def test_all_classes_use_same_constant(self):
        """
        All classes use the DEFAULT_DATA_NAMESPACE constant.
        """
        import inspect

        # Check IESTool
        ies_tool_sig = inspect.signature(ies.IESTool.__init__)
        ies_tool_default = ies_tool_sig.parameters['default_data_namespace'].default

        # Check RdfLibPlugin
        rdflib_sig = inspect.signature(RdfLibPlugin.__init__)
        rdflib_default = rdflib_sig.parameters['default_data_namespace'].default

        # Check SPARQLEndpointPlugin
        sparql_sig = inspect.signature(SPARQLEndpointPlugin.__init__)
        sparql_default = sparql_sig.parameters['default_data_namespace'].default

        # All should equal the constant
        self.assertEqual(
            ies_tool_default,
            ies_constants.DEFAULT_DATA_NAMESPACE,
            "IESTool should use DEFAULT_DATA_NAMESPACE constant"
        )
        self.assertEqual(
            rdflib_default,
            ies_constants.DEFAULT_DATA_NAMESPACE,
            "RdfLibPlugin should use DEFAULT_DATA_NAMESPACE constant"
        )
        self.assertEqual(
            sparql_default,
            ies_constants.DEFAULT_DATA_NAMESPACE,
            "SPARQLEndpointPlugin should use DEFAULT_DATA_NAMESPACE constant"
        )

    def test_generated_uris_use_configured_namespace(self):
        """
        Generated URIs use the configured default_data_namespace.
        """
        custom_namespace = "http://myorg.example.com/data#"
        tool = ies.IESTool(default_data_namespace=custom_namespace)

        # Create a person
        person = ies.Person(tool=tool, given_name="Bob", surname="Smith")

        # Verify the person's URI starts with the custom namespace
        self.assertTrue(
            person.uri.startswith(custom_namespace),
            f"Generated URI should start with {custom_namespace}, but got {person.uri}"
        )


if __name__ == '__main__':
    unittest.main()
