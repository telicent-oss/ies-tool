import re
import unittest
from urllib.parse import urlparse

import ies_tool.ies_constants as ies_constants

# A valid RDF local name (the part after the namespace separator): classes are
# PascalCase (e.g. LocationState) and properties are camelCase (e.g. holdsAccount).
LOCAL_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")

# Namespace bases in the module that constants are built on top of.
NAMESPACE_BASES = (ies_constants.IES_BASE,)


def _string_constants():
    """Yield (name, value) for every module-level string constant."""
    for name, value in vars(ies_constants).items():
        if name.isupper() and isinstance(value, str):
            yield name, value


def _namespaced_constants():
    """Yield (name, value, base) for constants built from a namespace base.

    Excludes the base constants themselves (e.g. IES_BASE).
    """
    bases = set(NAMESPACE_BASES)
    for name, value in _string_constants():
        if value in bases:
            continue
        for base in NAMESPACE_BASES:
            if value.startswith(base):
                yield name, value, base
                break


class TestConstantUris(unittest.TestCase):
    """Guard against malformed URI constants such as a stray extra '#'.

    Regression test for LOCATION_STATE, which was defined as
    f"{IES_BASE}#LocationState" — because IES_BASE already ends in '#', it
    produced the double-hash URI "http://ies.data.gov.uk/ontology/ies4##LocationState".
    """

    def test_namespaced_constants_discovered(self):
        """Sanity check that discovery actually finds the IES constants."""
        found = {name for name, _, _ in _namespaced_constants()}
        self.assertIn("LOCATION_STATE", found)
        self.assertIn("THING", found)

    def test_no_double_separator(self):
        """No constant should contain a doubled '#' or '//' outside the scheme."""
        for name, value in _string_constants():
            with self.subTest(constant=name):
                self.assertNotIn("##", value, f"{name} contains a doubled '#': {value}")
                # Strip the scheme's '//' before checking for stray doubled slashes.
                _, _, after_scheme = value.partition("://")
                self.assertNotIn(
                    "//", after_scheme,
                    f"{name} contains a doubled '/': {value}"
                )

    def test_namespaced_constant_is_base_plus_local_name(self):
        """A namespaced constant must be exactly its base followed by a valid local name."""
        for name, value, base in _namespaced_constants():
            with self.subTest(constant=name):
                local_name = value[len(base):]
                self.assertTrue(
                    local_name,
                    f"{name} has an empty local name: {value}"
                )
                self.assertRegex(
                    local_name, LOCAL_NAME_RE,
                    f"{name} has an invalid local name '{local_name}' in {value}. "
                    f"The local name must not include separators such as '#' or '/'."
                )

    def test_ies_constant_has_single_hash(self):
        """IES_BASE ends in '#', so its constants must contain exactly one '#'."""
        for name, value, base in _namespaced_constants():
            if base is not ies_constants.IES_BASE:
                continue
            with self.subTest(constant=name):
                self.assertEqual(
                    value.count("#"), 1,
                    f"{name} should contain exactly one '#' but is: {value}"
                )

    def test_all_string_constants_are_well_formed_uris(self):
        """Every string constant should parse as an absolute URI with no whitespace."""
        for name, value in _string_constants():
            with self.subTest(constant=name):
                self.assertNotRegex(
                    value, r"\s",
                    f"{name} contains whitespace: {value!r}"
                )
                parsed = urlparse(value)
                self.assertTrue(parsed.scheme, f"{name} has no URI scheme: {value}")
                self.assertTrue(parsed.netloc, f"{name} has no URI authority: {value}")


if __name__ == '__main__':
    unittest.main()
