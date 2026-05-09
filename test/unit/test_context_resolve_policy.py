import unittest
from pathlib import Path

from pilo import context
from pilo import paths
import pilotest


class TestContextResolvePolicy(unittest.TestCase):

    def test_resolve_delegates_to_storage_policy(self):
        cx = pilotest.make_context()

        resolved = cx.resolve(Path("in/file.txt"))

        self.assertEqual(resolved.physical, Path("/tmp/pile/in/file.txt"))
        self.assertEqual(resolved.dataset, "tank/a/pile")

    def test_resolve_collection(self):
        cx = pilotest.make_context()

        resolved = cx.resolve(Path("collection/a.jpg"))

        self.assertEqual(
            resolved.physical,
            Path("/tmp/static/collection/a.jpg"),
        )

    def test_resolve_filing(self):
        cx = pilotest.make_context()

        resolved = cx.resolve(Path("filing/x/y.pdf"))

        self.assertEqual(
            resolved.dataset,
            "tank/a/static/filing/x",
        )
