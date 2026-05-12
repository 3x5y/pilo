import unittest
from pathlib import Path
from unittest.mock import patch

from pilo.execution import (
    ExecutionPlan,
    ManifestOperation,
    execute_plan,
)

import pilotest


class TestExecutionPreview(unittest.TestCase):
    @patch("pilo.mutation_exec.execute_semantic_mutations")
    @patch("pilo.manifest_mutation.execute_manifest_mutations")
    def test_execute_plan_executes_mutations_first(self, mock_man, mock_sem):

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
