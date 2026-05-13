import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pilo.execution import (
    ExecutionPlan,
    ManifestOperation,
    ManifestStep,
    VerifyChecksumStep,
    execute_plan,
    execute_verify_checksum_step,
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


    @patch("pilo.mutation_exec.execute_semantic_mutations")
    @patch("pilo.execution.execute_verify_checksum_step")
    def test_preflight_executes_before_mutations(
        self,
        mock_verify,
        mock_mutate,
    ):

        order = []

        def verify(*args, **kwargs):
            order.append("verify")

        def mutate(*args, **kwargs):
            order.append("mutate")

        mock_verify.side_effect = verify
        mock_mutate.side_effect = mutate

        cx = pilotest.make_context()
        plan = ExecutionPlan(
            preflight_steps=[
                VerifyChecksumStep(
                    path=Path("/tmp/a"),
                    expected_checksum="abc",
                )
            ],
            semantic_mutations=["x"],
        )

        execute_plan(cx, plan)

        self.assertEqual(order, ["verify", "mutate"])


    @patch("pilo.mutation_exec.execute_semantic_mutations")
    @patch("pilo.execution.execute_verify_checksum_step")
    def test_preflight_failure_prevents_mutation(
        self,
        mock_verify,
        mock_mutate,
    ):

        def fail(*args, **kwargs):
            raise SystemExit(1)

        mock_verify.side_effect = fail

        cx = pilotest.make_context()

        plan = ExecutionPlan(
            preflight_steps=[
                VerifyChecksumStep(
                    path=Path("/tmp/a"),
                    expected_checksum="bad",
                )
            ],
            semantic_mutations=["x"],
        )

        with self.assertRaises(SystemExit):
            execute_plan(cx, plan)

        mock_mutate.assert_not_called()


class TestVerifyChecksumStep(pilotest.TestCase):

    def test_verify_checksum_step_accepts_matching_checksum(self):

        with tempfile.TemporaryDirectory() as td:

            path = Path(td) / "a.txt"
            path.write_text("hello")

            step = VerifyChecksumStep(
                path=path,
                expected_checksum=
                    "2cf24dba5fb0a30e26e83b2ac5b9e29"
                    "e1b161e5c1fa7425e73043362938b9824",
            )

            execute_verify_checksum_step(step)

    def test_verify_checksum_step_fails_on_mismatch(self):

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.txt"
            path.write_text("hello")
            step = VerifyChecksumStep(
                path=path,
                expected_checksum="bad",
            )
            with pilotest.assert_fatal(self):
                execute_verify_checksum_step(step)
