from pathlib import Path
import unittest

from pilo import paths
from pilo.context import StoragePolicy
import pilotest


class TestStoragePolicy(unittest.TestCase):

    def test_pile_policy(self):
        cx = pilotest.make_context()

        sp = StoragePolicy.for_domain(cx, paths.StorageDomain.PILE)

        self.assertEqual(sp.domain, paths.StorageDomain.PILE)
        self.assertEqual(sp.root_path, Path("/tmp/pile"))
        self.assertEqual(sp.root_dataset, "tank/a/pile")

    def test_collection_policy(self):
        cx = pilotest.make_context()

        sp = StoragePolicy.for_domain(cx, paths.StorageDomain.COLLECTION)

        self.assertEqual(sp.root_path, Path("/tmp/static/collection"))
        self.assertEqual(sp.root_dataset, "tank/a/static/collection")

    def test_filing_policy(self):
        cx = pilotest.make_context()

        sp = StoragePolicy.for_domain(cx, paths.StorageDomain.FILING)

        self.assertEqual(sp.root_path, Path("/tmp/static/filing"))
        self.assertEqual(sp.root_dataset, "tank/a/static/filing")

    def test_policy_physical_path(self):
        cx = pilotest.make_context()

        sp = StoragePolicy.for_domain(cx, paths.StorageDomain.COLLECTION)
        result = sp.physical_path(Path("photo.jpg"))

        self.assertEqual(result, Path("/tmp/static/collection/photo.jpg"))

    def test_policy_dataset_for_collection(self):
        cx = pilotest.make_context()

        sp = StoragePolicy.for_domain(cx, paths.StorageDomain.COLLECTION)
        result = sp.dataset_for(Path("photo.jpg"))

        self.assertEqual(result, "tank/a/static/collection")

    def test_policy_dataset_for_filing(self):
        cx = pilotest.make_context()

        sp = StoragePolicy.for_domain(cx, paths.StorageDomain.FILING)
        result = sp.dataset_for(Path("books/a.pdf"))

        self.assertEqual(result, "tank/a/static/filing/books")


class TestContextStoragePolicy(unittest.TestCase):

    def test_context_returns_pile_policy(self):
        cx = pilotest.make_context()

        sp = cx.storage_policy(paths.StorageDomain.PILE)

        self.assertEqual(sp.root_dataset, "tank/a/pile")

    def test_context_returns_collection_policy(self):
        cx = pilotest.make_context()

        sp = cx.storage_policy(paths.StorageDomain.COLLECTION)

        self.assertEqual(sp.root_dataset, "tank/a/static/collection")

    def test_context_returns_filing_policy(self):
        cx = pilotest.make_context()

        sp = cx.storage_policy(paths.StorageDomain.FILING)

        self.assertEqual(sp.root_dataset, "tank/a/static/filing")
