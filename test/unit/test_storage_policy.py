import unittest
from pathlib import Path

from pilo.storage_policy import StoragePolicy
from pilo import paths
import pilotest


class TestStoragePolicy(unittest.TestCase):

    def setUp(self):
        self.policy = StoragePolicy(
            pile_path=Path("/tmp/pile"),
            static_path=Path("/tmp/static"),
            pile_dataset="tank/a/pile",
            static_dataset="tank/a/static",
        )

    def test_map_pile(self):
        p = self.policy.resolve(
            paths.LogicalPath(
                domain=paths.StorageDomain.PILE,
                relpath=Path("in/a.txt"),
            )
        )

        self.assertEqual(p.physical, Path("/tmp/pile/in/a.txt"))
        self.assertEqual(p.dataset, "tank/a/pile")

    def test_map_collection(self):
        p = self.policy.resolve(
            paths.LogicalPath(
                domain=paths.StorageDomain.COLLECTION,
                relpath=Path("x.jpg"),
            )
        )

        self.assertEqual(p.physical, Path("/tmp/static/collection/x.jpg"))
        self.assertEqual(p.dataset, "tank/a/static/collection")

    def test_map_filing(self):
        p = self.policy.resolve(
            paths.LogicalPath(
                domain=paths.StorageDomain.FILING,
                relpath=Path("docs/a.pdf"),
            )
        )

        self.assertEqual(p.physical, Path("/tmp/static/filing/docs/a.pdf"))
        self.assertEqual(p.dataset, "tank/a/static/filing/docs")

    def test_invalid_domain_raises(self):
        with self.assertRaises(ValueError):
            self.policy.resolve(
                "not-a-logical-path"
            )
