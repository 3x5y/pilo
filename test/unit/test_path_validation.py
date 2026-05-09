from pathlib import Path
import unittest

from pilo import validation
import pilotest


class TestPathPolicyValidation(unittest.TestCase):

    def test_require_same_domain_accepts_pile_paths(self):
        validation.require_same_domain(
            Path("in/a.txt"),
            Path("out/a.txt"),
        )

    def test_require_same_domain_accepts_collection_paths(self):
        validation.require_same_domain(
            Path("collection/a.jpg"),
            Path("collection/b.jpg"),
        )

    def test_require_same_domain_rejects_cross_domain(self):
        with pilotest.assert_fatal(self):
            validation.require_same_domain(
                Path("in/a.txt"),
                Path("collection/a.txt"),
            )

    def test_require_same_domain_rejects_invalid_source(self):
        with pilotest.assert_fatal(self):
            validation.require_same_domain(
                Path("invalid/a"),
                Path("in/a"),
            )

    def test_require_same_domain_rejects_invalid_destination(self):
        with pilotest.assert_fatal(self):
            validation.require_same_domain(
                Path("in/a"),
                Path("invalid/a"),
            )
