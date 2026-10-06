import unittest
from pathlib import Path
from unittest.mock import patch

from pilo.content.execution import (
    ExecutionPlan,
    ManifestStep,
    execute_plan,
)


import pilotest


class TestExecutionPlan(pilotest.TestCase):
    @patch("pilo.content.mutation.execute_fs_mutations")
    @patch("pilo.content.manifest.execute_manifest_mutations")
    def test_execute_plan_skips_empty_sections(self,
                                               mock_manifest,
                                               mock_semantic):
        cx = pilotest.make_context()
        plan = ExecutionPlan()
        execute_plan(cx, plan)
        mock_semantic.assert_not_called()
        mock_manifest.assert_not_called()


    @patch("pilo.content.mutation.execute_fs_mutations")
    @patch("pilo.content.manifest.execute_manifest_mutations")
    def test_manifest_step_builds_after_mutations(self, mock_man, mock_sem):

        order = []

        def build():
            order.append("build")
            return []

        def semantic(*args, **kwargs):
            order.append("semantic")

        mock_sem.side_effect = semantic

        cx = pilotest.make_context()
        step = ManifestStep(
            subset="pile",
            manifest_path=Path("/tmp/p.manifest"),
            build_mutations=build,
        )
        plan = ExecutionPlan(
            filesystem_steps=["x"],
            manifest_steps=[step],
        )
        execute_plan(cx, plan)

        self.assertEqual(order, ["semantic", "build"])

    @patch("pilo.content.manifest.execute_manifest_mutations")
    def test_manifest_step_executes_generated_mutations(self, mock_exec):

        cx = pilotest.make_context()
        muts = [object()]
        step = ManifestStep(
            subset="pile",
            manifest_path=Path("/tmp/p.manifest"),
            build_mutations=lambda: muts,
        )
        plan = ExecutionPlan(manifest_steps=[step])
        execute_plan(cx, plan)

        mock_exec.assert_called_once_with(
            cx,
            "pile",
            Path("/tmp/p.manifest"),
            muts,
        )


    @patch("pilo.content.mutation.execute_fs_mutations")
    @patch("pilo.content.manifest.execute_manifest_mutations")
    @patch("pilo.fs.hash_file1")
    def test_execute_plan_does_not_verify_checksums(
        self,
        mock_hash,
        mock_manifest,
        mock_mutate,
    ):

        cx = pilotest.make_context()
        plan = ExecutionPlan(
            filesystem_steps=["x"],
            manifest_steps=[
                ManifestStep(
                    subset="pile",
                    manifest_path=Path("/tmp/p.manifest"),
                    build_mutations=lambda: [],
                )
            ],
        )

        execute_plan(cx, plan)

        mock_hash.assert_not_called()
