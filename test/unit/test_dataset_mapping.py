import unittest
from pilo import DatasetMapping


class TestDatasetMapping(unittest.TestCase):
    def test_root_mapping(self):
        m = DatasetMapping("tank/a", "backup/a")
        self.assertEqual(m.map("tank/a"), "backup/a")

    def test_child_mapping(self):
        m = DatasetMapping("tank/a", "backup/a")
        self.assertEqual(m.map("tank/a/foo"), "backup/a/foo")

    def test_inverse(self):
        m = DatasetMapping("tank/a", "backup/a")
        self.assertEqual(m.inverse("backup/a/foo"), "tank/a/foo")

    def test_validate_within_src_ok(self):
        m = DatasetMapping("tank/a", "backup/a")
        m.validate_within_src("tank/a/foo")

    def test_validate_within_src_fail(self):
        m = DatasetMapping("tank/a", "backup/a")
        with self.assertRaises(SystemExit):
            m.validate_within_src("tank/b/foo")

    def test_mapping_roundtrip(self):
        m = DatasetMapping("tank/a", "backup/a")
        src = "tank/a/foo/bar"
        dst = m.map(src)
        self.assertEqual(m.inverse(dst), src)


if __name__ == "__main__":
    unittest.main()
