import tempfile
import unittest
from pathlib import Path

from pilo import fs
import pilotest


class TestFilesystemPrimitives(unittest.TestCase):

    def test_ensure_parent_dir_creates_parents(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a" / "b" / "c.txt"

            cx = pilotest.make_context()

            fs.ensure_parent_dir(cx, path)

            self.assertTrue(
                (Path(td) / "a" / "b").is_dir()
            )

    def test_safe_copy_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            src = root / "src.txt"
            dst = root / "x" / "y" / "dst.txt"

            src.write_text("hello")

            cx = pilotest.make_context()

            fs.safe_copy(cx, src, dst)

            self.assertTrue(dst.is_file())
            self.assertEqual(
                dst.read_text(),
                "hello",
            )

    def test_safe_move_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            src = root / "src.txt"
            dst = root / "a" / "b" / "dst.txt"

            src.write_text("abc")

            cx = pilotest.make_context()

            fs.safe_move(cx, src, dst)

            self.assertFalse(src.exists())

            self.assertEqual(
                dst.read_text(),
                "abc",
            )

    def test_safe_unlink_removes_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x.txt"

            path.write_text("data")

            fs.safe_unlink(path)

            self.assertFalse(path.exists())

    def test_safe_copy_preserves_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            src = root / "src.txt"
            dst = root / "dst.txt"

            src.write_text("hello")

            cx = pilotest.make_context()

            fs.safe_copy(cx, src, dst)

            self.assertEqual(
                src.stat().st_size,
                dst.stat().st_size,
            )
