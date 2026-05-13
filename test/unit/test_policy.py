from pathlib import Path
import unittest

from pilo import policy
import pilotest


class TestPolicy(pilotest.TestCase):

    def test_require_child_dataset_accepts_child(self):
        policy.require_child_dataset("tank/a/static", "tank/a")

    def test_require_child_dataset_rejects_outside(self):
        with pilotest.assert_fatal(self):
            policy.require_child_dataset("tank/b", "tank/a")

    def test_require_relative_path_accepts_relative(self):
        policy.require_relative_path(Path("in/file.txt"))

    def test_require_relative_path_rejects_absolute(self):
        with pilotest.assert_fatal(self):
            policy.require_relative_path(Path("/etc/passwd"))

    def test_require_relative_path_rejects_parent_traversal(self):
        with pilotest.assert_fatal(self):
            policy.require_relative_path(Path("../secret"))

    def test_require_same_domain_accepts_same_domain(self):
        policy.require_same_domain(
            Path("in/a.txt"),
            Path("sort/b.txt"),
        )

    def test_require_same_domain_rejects_cross_domain(self):
        with pilotest.assert_fatal(self):
            policy.require_same_domain(
                Path("in/a.txt"),
                Path("collection/b.txt"),
            )

    def test_require_same_domain_accepts_pile_paths(self):
        policy.require_same_domain(
            Path("in/a.txt"),
            Path("out/a.txt"),
        )

    def test_require_same_domain_accepts_collection_paths(self):
        policy.require_same_domain(
            Path("collection/a.jpg"),
            Path("collection/b.jpg"),
        )

    def test_require_same_domain_rejects_cross_domain(self):
        with pilotest.assert_fatal(self):
            policy.require_same_domain(
                Path("in/a.txt"),
                Path("collection/a.txt"),
            )

    def test_require_same_domain_rejects_invalid_source(self):
        with pilotest.assert_fatal(self):
            policy.require_same_domain(
                Path("invalid/a"),
                Path("in/a"),
            )

    def test_require_same_domain_rejects_invalid_destination(self):
        with pilotest.assert_fatal(self):
            policy.require_same_domain(
                Path("in/a"),
                Path("invalid/a"),
            )
