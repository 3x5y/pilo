import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from pathlib import Path

import pilo
import pilotest


class TestPromotePlan(unittest.TestCase):

    def test_promote_op_model(self):
        op = pilo.PromoteOp(
            src=Path("/tmp/pile/out/collection/a.txt"),
            dst=Path("collection/a.txt"),
            dataset="tank/a/static/collection",
            action="copy",
        )

        self.assertEqual(op.action, "copy")
        self.assertEqual(op.dataset, "tank/a/static/collection")

    @patch("pilo.require_dataset")
    @patch("pilo.files_equal", return_value=True)
    def test_build_promote_plan(self, mock_equal, mock_require):
        cx = pilotest.make_context()

        src = cx.pile_path / "out/collection/a.txt"

        def iter_files():
            yield src
        with patch("pilo.iter_files", return_value=iter_files()):
            with patch.object(Path, "is_dir", return_value=True):
                with patch.object(Path, "iterdir", return_value=[]):

                    ops = pilo.build_promote_plan(cx)

        self.assertEqual(len(ops), 1)

        op = ops[0]

        self.assertEqual(op.src, src)
        self.assertEqual(op.dst, Path("collection/a.txt"))
        self.assertEqual(
            op.dataset,
            "tank/a/static/collection",
        )

    @patch("pilo.execute_semantic_mutations")
    def test_execute_uses_executor(self, mock_exec):
        cx = pilotest.make_context()

        ops = [
            pilo.PromoteOp(
                src=cx.pile_path / "out/collection/a.txt",
                dst=Path("collection/a.txt"),
                dataset="tank/a/static/collection",
                action="copy",
            )
        ]

        pilo.execute_promote_plan(cx, ops)
        mock_exec.assert_called_once()

    @patch("pilo.require_dataset")
    @patch("pilo.files_equal", return_value=True)
    def test_existing_identical_file_becomes_noop(
        self,
        mock_equal,
        mock_require,
    ):
        cx = pilotest.make_context()

        src = cx.pile_path / "out/collection/a.txt"

        resolved = pilo.Resolved(
            path=Path("/tmp/static/collection/a.txt"),
            dataset="tank/a/static/collection",
        )

        def iter_files():
            yield src
        with patch.object(cx, "resolve", return_value=resolved):
            with patch.object(Path, "is_file", return_value=True):
                with patch("pilo.iter_files", return_value=iter_files()):
                    with patch.object(Path, "is_dir", return_value=True):
                        with patch.object(Path, "iterdir", return_value=[]):

                            ops = pilo.build_promote_plan(cx)

        self.assertEqual(ops[0].action, "noop")
