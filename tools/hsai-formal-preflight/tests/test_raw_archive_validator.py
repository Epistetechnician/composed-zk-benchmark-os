import importlib.util
import io
import json
import pathlib
import unittest
from contextlib import redirect_stderr, redirect_stdout


MODULE_PATH = pathlib.Path(__file__).parents[1] / "raw_archive_validator.py"
SPEC = importlib.util.spec_from_file_location("raw_archive_validator", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RawArchiveValidatorTests(unittest.TestCase):
    def test_self_test_measures_exactly_31_cases(self):
        result = MODULE.run_self_test()
        self.assertEqual(result["passed"], 31)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(len(result["cases"]), 31)
        self.assertEqual(len(set(result["cases"])), 31)

    def test_self_test_cli_is_canonical_json(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = MODULE.main(["self-test"])
        self.assertEqual(status, 0)
        self.assertEqual(stderr.getvalue(), "")
        decoded = json.loads(stdout.getvalue())
        self.assertEqual(decoded["schema"], MODULE.SELF_TEST_SCHEMA)
        self.assertEqual(stdout.getvalue(), MODULE.canonical_json(decoded) + "\n")

    def test_structural_inventory_binds_order_and_raw_name(self):
        rows = [[0, "./a", "a", "regular", 0], [1, "b/", "b", "directory", 0]]
        first = MODULE.structural_inventory(rows)
        self.assertEqual(first, "cb37bb705c1635c6198722e2edb22a9afe4c56a8dd320f6da7904b101fd5dbc2")
        reordered = [[0, "b/", "b", "directory", 0], [1, "./a", "a", "regular", 0]]
        self.assertNotEqual(first, MODULE.structural_inventory(reordered))
        changed = [[0, "a", "a", "regular", 0], rows[1]]
        self.assertNotEqual(first, MODULE.structural_inventory(changed))

    def test_duplicate_pax_keys_fail_before_dictionary_collapse(self):
        payload = MODULE.pax_record("path", "a") + MODULE.pax_record("path", "b")
        with self.assertRaises(MODULE.ValidationError) as raised:
            MODULE.parse_pax(payload)
        self.assertEqual(raised.exception.code, "duplicate_pax_key")

    def test_normalize_rejects_regular_ancestor_alias_components(self):
        with self.assertRaises(MODULE.ValidationError) as raised:
            MODULE.normalize_name("a/../b", MODULE.tarfile.REGTYPE, 0)
        self.assertEqual(raised.exception.code, "parent_component")


if __name__ == "__main__":
    unittest.main()
