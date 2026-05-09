from pathlib import Path
import unittest

from pilo import mutation


class TestMutationManifestDomains(unittest.TestCase):

    def test_pile_dataset_maps_to_pile(self):

        muts = [
            mutation.SemanticMutation(
                action="move",
                src=Path("/a"),
                dst=Path("/b"),
                dataset="tank/a/pile",
            )
        ]

        result = mutation.mutation_manifest_domains(muts)

        self.assertEqual(result, {"pile"})

    def test_collection_dataset_maps_to_collection(self):

        muts = [
            mutation.SemanticMutation(
                action="move",
                src=Path("/a"),
                dst=Path("/b"),
                dataset="tank/a/static/collection",
            )
        ]

        result = mutation.mutation_manifest_domains(muts)

        self.assertEqual(result, {"collection"})

    def test_filing_dataset_maps_to_filing(self):

        muts = [
            mutation.SemanticMutation(
                action="move",
                src=Path("/a"),
                dst=Path("/b"),
                dataset="tank/a/static/filing/docs",
            )
        ]

        result = mutation.mutation_manifest_domains(muts)

        self.assertEqual(result, {"filing"})

    def test_unknown_dataset_ignored(self):

        muts = [
            mutation.SemanticMutation(
                action="move",
                src=Path("/a"),
                dst=Path("/b"),
                dataset="tank/a/unknown",
            )
        ]

        result = mutation.mutation_manifest_domains(muts)

        self.assertEqual(result, set())

    def test_duplicate_domains_collapsed(self):

        muts = [
            mutation.SemanticMutation(
                action="move",
                src=Path("/a"),
                dst=Path("/b"),
                dataset="tank/a/pile",
            ),
            mutation.SemanticMutation(
                action="copy",
                src=Path("/c"),
                dst=Path("/d"),
                dataset="tank/a/pile",
            ),
        ]

        result = mutation.mutation_manifest_domains(muts)

        self.assertEqual(result, {"pile"})
