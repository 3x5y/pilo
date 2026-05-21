import hashlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from pilo.front import checksum
from pilo import context
from pilo import fs
from pilo.front import manifest
from pilo.front import manifest
from pilo.front import manifest
from pilo.front import manifest
from pilo.front import mutation
from pilo import status
from pilo.front import ingest
import pilotest


class TestManifest(pilotest.TestCase):

    def test_sha256_file_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.txt"
            path.write_bytes(b"hello world")

            expected = hashlib.sha256(b"hello world").hexdigest()

            self.assertEqual(fs.sha256_file(path), expected)

    def test_sha256_file_empty(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "empty"
            path.write_bytes(b"")

            expected = hashlib.sha256(b"").hexdigest()

            self.assertEqual(fs.sha256_file(path), expected)

    def test_generate_manifest_lines_sorted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "z.txt").write_text("z")
            (root / "a.txt").write_text("a")

            lines = list(manifest.generate_manifest_lines(root))

            self.assertEqual(
                [line.split("  ./")[1] for line in lines],
                ["a.txt", "z.txt"],
            )

    def test_generate_manifest_lines_relative_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sub = root / "dir"
            sub.mkdir()
            f = sub / "x.txt"
            f.write_text("abc")

            lines = list(manifest.generate_manifest_lines(root))

            self.assertEqual(len(lines), 1)
            line = lines[0]
            self.assertTrue(line.endswith("  ./dir/x.txt"))

    def test_generate_manifest_lines_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            lines = list(manifest.generate_manifest_lines(root))

            self.assertEqual(lines, [])

    def test_verify_manifest_lines_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(manifest.generate_manifest_lines(root))

            self.assertTrue(manifest.verify_manifest_lines(root, lines))

    def test_verify_manifest_lines_detects_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(manifest.generate_manifest_lines(root))
            f.write_text("changed")

            self.assertFalse(manifest.verify_manifest_lines(root, lines))

    def test_verify_manifest_lines_detects_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(manifest.generate_manifest_lines(root))

            f.unlink()

            self.assertFalse(manifest.verify_manifest_lines(root, lines))

    @patch("sys.exit")
    @patch("pilo.status.render_validation_report")
    @patch("pilo.status.collect_manifest_validation")
    def test_manifest_verify_uses_status_system(
        self,
        mock_check,
        mock_render,
        mock_exit,
    ):
        cx = pilotest.make_context()
        mod = pilotest.import_command("manifest-verify")

        with patch("pilo.context.Context", return_value=cx):
            mod.main()

        mock_check.assert_called_once()
        mock_render.assert_called_once()
        mock_exit.assert_called_once()

    @patch("sys.exit")
    @patch("pilo.status.check_manifest")
    @patch("pilo.status.render_validation_report", return_value=["OK"])
    @patch("builtins.print")
    def test_manifest_verify_renders_messages(self, mock_print, *_):
        cx = pilotest.make_context()
        mod = pilotest.import_command("manifest-verify")
        with patch("pilo.context.Context", return_value=cx):
            mod.main()

        mock_print.assert_called_once_with("OK")

    def test_checksum_provenance_values(self):
        p = manifest.ChecksumProvenance
        self.assertEqual(p.MANIFEST.value, "manifest")
        self.assertEqual(p.VERIFIED.value, "verified")
        self.assertEqual(p.GENERATED.value, "generated")

    def test_reuse_manifest_checksum_marks_manifest(self):

        entry = manifest.ManifestEntry(
            checksum="abc123",
            path=Path("a.txt"),
        )

        item = checksum.reuse_manifest_checksum(entry)

        self.assertEqual(
            item.provenance,
            (
                manifest
                .ChecksumProvenance
                .MANIFEST
            ),
        )

class TestManifestEntries(pilotest.TestCase):

    def test_manifest_entry_model(self):

        entry = manifest.ManifestEntry(
            checksum="abc123",
            path=Path("a.txt"),
        )

        self.assertEqual(entry.checksum, "abc123")
        self.assertEqual(entry.path, Path("a.txt"))

    def test_render_manifest_entry(self):

        entry = manifest.ManifestEntry(
            checksum="deadbeef",
            path=Path("dir/file.txt"),
        )

        line = manifest.render_manifest_entry(entry)

        self.assertEqual(
            line,
            "deadbeef  ./dir/file.txt",
        )

    def test_parse_manifest_line(self):

        entry = manifest.parse_manifest_line(
            "abc123  ./dir/file.txt"
        )

        self.assertEqual(entry.checksum, "abc123")
        self.assertEqual(
            entry.path,
            Path("dir/file.txt"),
        )

    def test_parse_manifest_line_rejects_invalid(self):

        with self.assertRaises(ValueError):
            manifest.parse_manifest_line(
                "invalid line"
            )

    def test_generate_manifest_entries(self):

        with pilotest.tmpdir() as td:
            root = td / "capture"
            root.mkdir()

            path = root / "a.txt"
            path.write_text("hello")

            entries = list(
                manifest.generate_manifest_entries(root)
            )

            self.assertEqual(len(entries), 1)

            entry = entries[0]

            self.assertEqual(entry.path, Path("a.txt"))

    def test_load_manifest_entries(self):

        with pilotest.tmpdir() as td:
            mf = td / "test.manifest"

            mf.write_text(
                "aaa  ./a.txt\n"
                "bbb  ./b.txt\n"
            )

            entries = manifest.load_manifest_entries(mf)

            self.assertEqual(len(entries), 2)

            self.assertEqual(
                entries[0].path,
                Path("a.txt"),
            )

            self.assertEqual(
                entries[1].checksum,
                "bbb",
            )

    def test_render_manifest_lines(self):

        entries = [
            manifest.ManifestEntry(
                checksum="aaa",
                path=Path("a.txt"),
            ),
            manifest.ManifestEntry(
                checksum="bbb",
                path=Path("b.txt"),
            ),
        ]

        lines = list(
            manifest.render_manifest_lines(entries)
        )

        self.assertEqual(
            lines,
            [
                "aaa  ./a.txt",
                "bbb  ./b.txt",
            ]
        )


class TestManifestMutation(pilotest.TestCase):

    def test_manifest_add_entry_mutation(self):

        mut = manifest.ManifestAddEntry(
            subset="pile",
            entry=manifest.ManifestEntry(
                checksum="abc",
                path=Path("in/a.txt"),
            )
        )

        self.assertEqual(mut.subset, "pile")
        self.assertEqual(
            mut.entry.path,
            Path("in/a.txt"),
        )

    def test_manifest_remove_entry_mutation(self):

        mut = manifest.ManifestRemoveEntry(
            subset="pile",
            path=Path("in/a.txt"),
        )

        self.assertEqual(mut.subset, "pile")
        self.assertEqual(mut.path, Path("in/a.txt"))

    def test_apply_manifest_add_entry(self):

        entries = []

        mut = manifest.ManifestAddEntry(
            subset="pile",
            entry=manifest.ManifestEntry(
                checksum="abc",
                path=Path("in/a.txt"),
            )
        )

        out = manifest.apply_manifest_mutations(
            entries,
            [mut],
        )

        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].checksum, "abc")

    def test_apply_manifest_remove_entry(self):

        entries = [
            manifest.ManifestEntry(
                checksum="abc",
                path=Path("in/a.txt"),
            ),
            manifest.ManifestEntry(
                checksum="def",
                path=Path("in/b.txt"),
            ),
        ]

        mut = manifest.ManifestRemoveEntry(
            subset="pile",
            path=Path("in/a.txt"),
        )

        out = manifest.apply_manifest_mutations(
            entries,
            [mut],
        )

        self.assertEqual(len(out), 1)
        self.assertEqual(
            out[0].path,
            Path("in/b.txt"),
        )

    def test_apply_manifest_add_replaces_existing_path(self):

        entries = [
            manifest.ManifestEntry(
                checksum="old",
                path=Path("in/a.txt"),
            )
        ]

        mut = manifest.ManifestAddEntry(
            subset="pile",
            entry=manifest.ManifestEntry(
                checksum="new",
                path=Path("in/a.txt"),
            )
        )

        out = manifest.apply_manifest_mutations(
            entries,
            [mut],
        )

        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].checksum, "new")


class TestManifestStore(pilotest.TestCase):
    def test_write_manifest_entries(self):

        with pilotest.make_tmp_context() as cx:

            out = cx.path / "test.manifest"

            entries = [
                manifest.ManifestEntry(
                    checksum="abc",
                    path=Path("in/a.txt"),
                )
            ]

            manifest.write_manifest_entries(
                cx,
                out,
                entries,
            )

            lines = out.read_text().splitlines()

            self.assertEqual(
                lines,
                ["abc  ./in/a.txt"]
            )

    def test_write_manifest(self):
        cx = pilotest.make_context()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            (root / "a.txt").write_text("hello")

            mfile = root / "test.manifest"

            manifest.write_manifest(cx, root, mfile)

            self.assertTrue(mfile.exists())

            text = mfile.read_text()

            self.assertIn("./a.txt", text)

    def test_write_manifest_entries_overwrites_existing(self):

        with pilotest.make_tmp_context() as cx:
            out = cx.path / "test.manifest"
            out.write_text("old data\n")
            entries = [
                manifest.ManifestEntry(
                    checksum="abc",
                    path=Path("in/a.txt"),
                )
            ]

            manifest.write_manifest_entries(cx, out, entries)
            text = out.read_text()
            self.assertEqual(text, "abc  ./in/a.txt\n")


class TestManifestPolicy(pilotest.TestCase):

    def test_manifest_subset_root(self):
        cx = pilotest.make_context()

        self.assertEqual(
            manifest.manifest_subset_root(
                cx,
                "pile",
            ),
            cx.pile_path,
        )

        self.assertEqual(
            manifest.manifest_subset_root(
                cx,
                "collection",
            ),
            cx.static_path / "collection",
        )

        self.assertEqual(
            manifest.manifest_subset_root(
                cx,
                "filing",
            ),
            cx.static_path / "filing",
        )

    def test_dataset_manifest_subset_pile(self):

        result = (
            manifest.dataset_manifest_subset(
                "tank/a/pile"
            )
        )

        self.assertEqual(result, "pile")

    def test_dataset_manifest_subset_collection(self):

        result = (
            manifest.dataset_manifest_subset(
                "tank/a/static/collection"
            )
        )

        self.assertEqual(result, "collection")

    def test_dataset_manifest_subset_filing(self):

        result = (
            manifest.dataset_manifest_subset(
                "tank/a/static/filing/docs"
            )
        )

        self.assertEqual(result, "filing")

    def test_dataset_manifest_subset_unknown(self):

        result = (
            manifest.dataset_manifest_subset(
                "tank/a/unknown"
            )
        )

        self.assertIsNone(result)


class TestManifestUpdate(pilotest.TestCase):

    def test_build_manifest_update_plan(self):
        cx = pilotest.make_context()

        plan = manifest.build_manifest_update_plan(
            cx,
            ["pile", "collection"],
        )

        self.assertEqual(
            [s.name for s in plan.subsets],
            ["pile", "collection"],
        )

    @patch("pilo.front.manifest.write_manifest")
    @patch("pilo.front.manifest.commit_manifest_if_changed")
    @patch("pilo.fs.ensure_parent_dir")
    def test_execute_manifest_update_plan(
        self,
        mock_dir,
        mock_commit,
        mock_write,
    ):
        cx = pilotest.make_context()

        plan = (
            manifest
            .build_manifest_update_plan(
                cx,
                ["pile"],
            )
        )

        manifest.execute_manifest_update_plan(
            cx,
            plan,
        )

        mock_write.assert_called_once()
        mock_commit.assert_called_once()

    def test_write_manifest(self):
        cx = pilotest.make_context()

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            (root / "a.txt").write_text(
                "hello"
            )

            mfile = root / "test.manifest"

            manifest.write_manifest(
                cx,
                root,
                mfile,
            )

            self.assertTrue(mfile.exists())

            text = mfile.read_text()

            self.assertIn("./a.txt", text)

    @patch("pilo.git.commit_if_changed")
    @patch("pilo.git.ensure_repo")
    def test_commit_manifest_if_changed(
        self,
        mock_repo,
        mock_commit,
    ):
        cx = pilotest.make_context()

        mfile = Path("/tmp/test.manifest")

        manifest.commit_manifest_if_changed(
            cx,
            mfile,
            "test update",
        )

        mock_repo.assert_called_once()

        mock_commit.assert_called_once()


class TestManifestIndex(pilotest.TestCase):

    def test_lookup_returns_entry(self):

        entry = manifest.ManifestEntry(
            checksum="abc123",
            path=Path("in/a.txt"),
        )
        index = manifest.ManifestIndex([entry])
        result = index.lookup(Path("in/a.txt"))

        self.assertEqual(result, entry)

    def test_lookup_missing_returns_none(self):
        index = manifest.ManifestIndex([])
        result = index.lookup(Path("missing.txt"))
        self.assertIsNone(result)


    def test_require_returns_entry(self):
        entry = manifest.ManifestEntry(
            checksum="abc123",
            path=Path("in/a.txt"),
        )
        index = manifest.ManifestIndex([entry])
        result = index.require(Path("in/a.txt"))
        self.assertEqual(result, entry)

    def test_require_missing_fails(self):
        index = manifest.ManifestIndex([])
        with pilotest.assert_fatal(self):
            index.require(Path("missing.txt"))

    def test_duplicate_paths_last_entry_wins(self):
        old = manifest.ManifestEntry(
            checksum="old",
            path=Path("in/a.txt"),
        )
        new = manifest.ManifestEntry(
            checksum="new",
            path=Path("in/a.txt"),
        )
        index = manifest.ManifestIndex([old, new])
        result = index.lookup(Path("in/a.txt"))
        self.assertEqual(result, new)
