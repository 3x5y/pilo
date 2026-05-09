import unittest
from pathlib import Path

from pilo import error
from pilo import paths
import pilotest


class TestLogicalPaths(unittest.TestCase):

    def test_parse_pile_path(self):
        lp = paths.parse_logical_path(Path("in/a.txt"))

        self.assertEqual(lp.domain, paths.StorageDomain.PILE)
        self.assertEqual(lp.relpath, Path("in/a.txt"))

    def test_parse_collection_path(self):
        lp = paths.parse_logical_path(Path("collection/photo.jpg"))

        self.assertEqual(lp.domain, paths.StorageDomain.COLLECTION)
        self.assertEqual(lp.relpath, Path("photo.jpg"))

    def test_parse_filing_path(self):
        lp = paths.parse_logical_path(Path("filing/docs/report.pdf"))

        self.assertEqual(lp.domain, paths.StorageDomain.FILING)
        self.assertEqual(lp.relpath, Path("docs/report.pdf"))

    def test_reject_empty_path(self):
        with pilotest.assert_fatal(self):
            paths.parse_logical_path(Path())

    def test_reject_invalid_domain(self):
        with pilotest.assert_fatal(self):
            paths.parse_logical_path(Path("random/file.txt"))

    def test_reject_parent_traversal(self):
        with pilotest.assert_fatal(self):
            paths.parse_logical_path(Path("../secret"))

    def test_resolve_pile_path(self):
        cx = pilotest.make_context()

        r = cx.resolve(Path("in/a.txt"))

        self.assertEqual(r.logical.domain, paths.StorageDomain.PILE)
        self.assertEqual(r.physical, Path("/tmp/pile/in/a.txt"))
        self.assertEqual(r.dataset, "tank/a/pile")

    def test_resolve_collection_path(self):
        cx = pilotest.make_context()

        r = cx.resolve(Path("collection/x.jpg"))

        self.assertEqual(r.logical.domain, paths.StorageDomain.COLLECTION)
        self.assertEqual(r.physical, Path("/tmp/static/collection/x.jpg"))
        self.assertEqual(r.dataset, "tank/a/static/collection")

    def test_resolve_filing_path(self):
        cx = pilotest.make_context()

        r = cx.resolve(Path("filing/books/a.pdf"))

        self.assertEqual(r.logical.domain, paths.StorageDomain.FILING)
        self.assertEqual(r.physical, Path("/tmp/static/filing/books/a.pdf"))
        self.assertEqual(r.dataset, "tank/a/static/filing/books")

    def test_validate_relative_path_accepts_relative(self):
        paths.validate_relative_path(Path("a/b"))

    def test_validate_relative_path_rejects_absolute(self):
        with self.assertRaises(paths.PathParseError):
            paths.validate_relative_path(Path("/etc/passwd"))

    def test_validate_relative_path_rejects_parent_traversal(self):
        with self.assertRaises(paths.PathParseError):
            paths.validate_relative_path(Path("../secret"))

    def test_parse_logical_path_raises_parse_error(self):
        with self.assertRaises(paths.PathParseError):
            paths._parse_logical_path(Path("random/file.txt"))

    def test_parse_logical_path_raises_fatal_error(self):
        with self.assertRaises(error.FatalError):
            paths.parse_logical_path(Path("random/file.txt"))
