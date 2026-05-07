import unittest
from pathlib import Path

import pilo
import pilotest


class TestLogicalPaths(unittest.TestCase):

    def test_parse_pile_path(self):
        lp = pilo.parse_logical_path(Path("in/a.txt"))

        self.assertEqual(lp.domain, pilo.StorageDomain.PILE)
        self.assertEqual(lp.relpath, Path("in/a.txt"))

    def test_parse_collection_path(self):
        lp = pilo.parse_logical_path(Path("collection/photo.jpg"))

        self.assertEqual(lp.domain, pilo.StorageDomain.COLLECTION)
        self.assertEqual(lp.relpath, Path("photo.jpg"))

    def test_parse_filing_path(self):
        lp = pilo.parse_logical_path(
            Path("filing/docs/report.pdf")
        )

        self.assertEqual(lp.domain, pilo.StorageDomain.FILING)
        self.assertEqual(
            lp.relpath,
            Path("docs/report.pdf"),
        )

    def test_reject_empty_path(self):
        with self.assertRaises(SystemExit):
            pilo.parse_logical_path(Path())

    def test_reject_invalid_domain(self):
        with self.assertRaises(SystemExit):
            pilo.parse_logical_path(Path("random/file.txt"))

    def test_reject_parent_traversal(self):
        with self.assertRaises(SystemExit):
            pilo.parse_logical_path(Path("../secret"))

    def test_resolve_pile_path(self):
        cx = pilotest.make_context()

        r = cx.resolve(Path("in/a.txt"))

        self.assertEqual(
            r.logical.domain,
            pilo.StorageDomain.PILE,
        )

        self.assertEqual(
            r.physical,
            Path("/tmp/pile/in/a.txt"),
        )

        self.assertEqual(
            r.dataset,
            "tank/a/pile",
        )

    def test_resolve_collection_path(self):
        cx = pilotest.make_context()

        r = cx.resolve(Path("collection/x.jpg"))

        self.assertEqual(
            r.logical.domain,
            pilo.StorageDomain.COLLECTION,
        )

        self.assertEqual(
            r.physical,
            Path("/tmp/static/collection/x.jpg"),
        )

        self.assertEqual(
            r.dataset,
            "tank/a/static/collection",
        )

    def test_resolve_filing_path(self):
        cx = pilotest.make_context()

        r = cx.resolve(Path("filing/books/a.pdf"))

        self.assertEqual(
            r.logical.domain,
            pilo.StorageDomain.FILING,
        )

        self.assertEqual(
            r.physical,
            Path("/tmp/static/filing/books/a.pdf"),
        )

        self.assertEqual(
            r.dataset,
            "tank/a/static/filing/books",
        )
