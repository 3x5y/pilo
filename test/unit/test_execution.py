import unittest
from pathlib import Path
from unittest.mock import patch

from pilo.execution import (
    ExecutionPlan,
    ManifestOperation,
    ManifestStep,
    execute_plan,
)

import pilotest


class TestExecutionPlan(pilotest.TestCase):
    @patch("pilo.mutation_exec.execute_semantic_mutations")
    @patch("pilo.manifest_mutation.execute_manifest_mutations")
    def _test_execute_plan_executes_mutations_first(self, mock_man, mock_sem):

        order = []
        def semantic(*args, **kw):
            order.append("semantic")

        def manifest(*args, **kw):
            order.append("manifest")

        mock_sem.side_effect = semantic
        mock_man.side_effect = manifest

        cx = pilotest.make_context()
        plan = ExecutionPlan(
            semantic_mutations=["dummy"],
            manifest_operations=[
                ManifestOperation(
                    subset="pile",
                    manifest_path=Path("/tmp/pile.manifest"),
                    mutations=[],
                )
            ],
        )
        execute_plan(cx, plan)

        self.assertEqual(order, ["semantic", "manifest"])

        
    @patch("pilo.mutation.execute_semantic_mutations")
    @patch("pilo.manifest_mutation.execute_manifest_mutations")
    def test_execute_plan_skips_empty_sections(self,
                                               mock_manifest,
                                               mock_semantic):
        cx = pilotest.make_context()
        plan = ExecutionPlan()
        execute_plan(cx, plan)
        mock_semantic.assert_not_called()
        mock_manifest.assert_not_called()


    @patch("pilo.mutation_exec.execute_semantic_mutations")
    @patch("pilo.manifest_mutation.execute_manifest_mutations")
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
            semantic_mutations=["x"],
            manifest_steps=[step],
        )
        execute_plan(cx, plan)

        self.assertEqual(order, ["semantic", "build"])

    @patch("pilo.manifest_mutation.execute_manifest_mutations")
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
