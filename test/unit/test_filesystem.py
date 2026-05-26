import hashlib
import unittest

from pilo import fs
import pilotest


class TestFilesystemPrimitives(pilotest.TestCase):

    def test_ensure_parent_dir_creates_parents(self):
        with pilotest.tmpdir() as root:
            path = root / "a" / "b" / "c.txt"
            cx = pilotest.make_context()

            fs.ensure_parent_dir(cx, path)

            self.assertTrue((root / "a" / "b").is_dir())

    def test_safe_copy_creates_parent_dirs(self):
        with pilotest.tmpdir() as root:
            src = root / "src.txt"
            dst = root / "x" / "y" / "dst.txt"
            src.write_text("hello")
            cx = pilotest.make_context()

            fs.safe_copy(cx, src, dst)

            self.assertTrue(dst.is_file())
            self.assertEqual(dst.read_text(), "hello")

    def test_safe_move_creates_parent_dirs(self):
        with pilotest.tmpdir() as root:
            src = root / "src.txt"
            dst = root / "a" / "b" / "dst.txt"
            src.write_text("abc")
            cx = pilotest.make_context()
            fs.safe_move(cx, src, dst)

            self.assertFalse(src.exists())
            self.assertEqual(dst.read_text(), "abc")

    def test_safe_unlink_removes_file(self):
        with pilotest.tmpdir() as root:
            path = root / "x.txt"
            path.write_text("data")

            fs.safe_unlink(path)

            self.assertFalse(path.exists())

    def test_safe_copy_preserves_metadata(self):
        with pilotest.tmpdir() as root:
            src = root / "src.txt"
            dst = root / "dst.txt"
            src.write_text("hello")
            cx = pilotest.make_context()

            fs.safe_copy(cx, src, dst)

            self.assertEqual(src.stat().st_size, dst.stat().st_size)

    def test_iter_files(self):
        with pilotest.tmpdir() as root:
            path = root / "a.txt"
            path.write_text("a")

            files = list(fs.iter_files(root))

            self.assertEqual(files, [path])

    def test_hash_file1(self):
        with pilotest.tmpdir() as root:
            path = root / "a.txt"
            path.write_text("hello")
            h = hashlib.sha256(b"hello").hexdigest()
            result = fs.hash_file1(path)

            self.assertEqual(result, h)

    def test_files_equal(self):
        with pilotest.tmpdir() as root:
            a = root / "a.txt"
            b = root / "b.txt"

            a.write_text("same")
            b.write_text("same")

            self.assertTrue(fs.files_equal(a, b))
