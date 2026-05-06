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

if __name__ == "__main__":
    unittest.main()
