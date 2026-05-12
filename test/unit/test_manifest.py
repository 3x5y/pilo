import hashlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from pilo import context
from pilo import fs
from pilo import manifest
from pilo import manifest_codec
from pilo import manifest_model
from pilo import manifest_mutation
from pilo import manifest_policy
from pilo import manifest_status
from pilo import manifest_store
from pilo import manifest_update
from pilo import manifest_verify
from pilo import mutation
from pilo import status
from pilo.front import ingest
import pilotest


class TestManifest(unittest.TestCase):

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

            lines = list(manifest_verify.generate_manifest_lines(root))

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

            lines = list(manifest_verify.generate_manifest_lines(root))

            self.assertEqual(len(lines), 1)
            line = lines[0]
            self.assertTrue(line.endswith("  ./dir/x.txt"))

    def test_generate_manifest_lines_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            lines = list(manifest_verify.generate_manifest_lines(root))

            self.assertEqual(lines, [])

    def test_verify_manifest_lines_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(manifest_verify.generate_manifest_lines(root))

            self.assertTrue(manifest_verify.verify_manifest_lines(root, lines))

    def test_verify_manifest_lines_detects_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(manifest_verify.generate_manifest_lines(root))
            f.write_text("changed")

            self.assertFalse(manifest_verify.verify_manifest_lines(root, lines))

    def test_verify_manifest_lines_detects_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(manifest_verify.generate_manifest_lines(root))

            f.unlink()

            self.assertFalse(manifest_verify.verify_manifest_lines(root, lines))

    def test_manifest_verify_op_model(self):
        op = manifest_status.ManifestVerifyOp(
            subset="pile",
            root=Path("/tmp/pile"),
            manifest=Path("/tmp/admin/manifest/pile.manifest"),
        )

        self.assertEqual(op.subset, "pile")
        self.assertEqual(op.root, Path("/tmp/pile"))
        self.assertEqual(op.manifest, Path("/tmp/admin/manifest/pile.manifest"))

    def test_build_manifest_verify_plan(self):
        cx = pilotest.make_context()

        ops = manifest_status.build_manifest_verify_plan(
            cx,
            ["pile", "collection"],
        )

        self.assertEqual(len(ops), 2)
        self.assertEqual(ops[0].root, cx.pile_path)
        self.assertEqual(ops[1].root, cx.static_path / "collection")
        self.assertEqual(ops[0].manifest, cx.admin_path / "manifest/pile.manifest")

    @patch("subprocess.run")
    def test_verify_manifest_op(self, mock_run):
        op = manifest_status.ManifestVerifyOp(
            subset="pile",
            root=Path("/tmp/pile"),
            manifest=Path("/tmp/pile.manifest"),
        )

        with patch.object(Path, "is_file", return_value=True):
            with patch.object(
                Path,
                "stat",
            ) as mock_stat:

                mock_stat.return_value.st_size = 123

                manifest_status.verify_manifest_op(op)

        mock_run.assert_called_once()

    @patch("pilo.manifest_status.verify_manifest_op")
    def test_execute_manifest_verify_plan(
        self,
        mock_verify,
    ):
        ops = [
            manifest_status.ManifestVerifyOp(
                subset="pile",
                root=Path("/tmp/pile"),
                manifest=Path("/tmp/pile.manifest"),
            )
        ]

        manifest_status.execute_manifest_verify_plan(ops)

        mock_verify.assert_called_once()

    @patch("subprocess.run")
    def test_verify_manifest_failure_raises_fatal(
        self,
        mock_run,
    ):
        op = manifest_status.ManifestVerifyOp(
            subset="pile",
            root=Path("/tmp/pile"),
            manifest=Path("/tmp/pile.manifest"),
        )

        mock_run.side_effect = subprocess.CalledProcessError(
            1,
            ["sha256sum"],
        )

        with patch.object(Path, "is_file", return_value=True):
            with patch.object(Path, "stat") as mock_stat:

                mock_stat.return_value.st_size = 1

                with pilotest.assert_fatal(self):
                    manifest_status.verify_manifest_op(op)

    @patch("sys.exit")
    @patch("pilo.status.render_system_status")
    @patch("pilo.status.check_manifest_status")
    def test_manifest_verify_uses_status_system(
        self,
        mock_check,
        mock_render,
        mock_exit,
    ):
        cx = pilotest.make_context()

        with patch("pilo.context.Context", return_value=cx):
            mod = pilotest.import_command(
                "manifest-verify"
            )

            mod.main()

        mock_check.assert_called_once()
        mock_render.assert_called_once()
        mock_exit.assert_called_once()

    @patch("sys.exit")
    @patch("pilo.status.render_system_status")
    def test_manifest_verify_returns_status_code(
        self,
        mock_render,
        mock_exit,
    ):
        cx = pilotest.make_context()

        st = status.SystemStatus()
        st.code = 1

        with patch("pilo.context.Context", return_value=cx):
            with patch(
                "pilo.status.check_manifest_status",
                side_effect=lambda cx, s: setattr(s, "code", 1),
            ):
                mod = pilotest.import_command(
                    "manifest-verify"
                )

                mod.main()

        mock_exit.assert_called_once_with(1)

    @patch("builtins.print")
    @patch("sys.exit")
    @patch("pilo.status.check_manifest_status")
    @patch(
        "pilo.status.render_system_status",
        return_value=["OK: manifest: pile verified"],
    )
    def test_manifest_verify_renders_messages(
        self,
        mock_render,
        mock_check,
        mock_exit,
        mock_print,
    ):
        cx = pilotest.make_context()

        with patch("pilo.context.Context", return_value=cx):
            mod = pilotest.import_command(
                "manifest-verify"
            )

            mod.main()

        mock_print.assert_called_once_with(
            "OK: manifest: pile verified"
        )


class TestManifestEntries(unittest.TestCase):

    def test_manifest_entry_model(self):

        entry = manifest_model.ManifestEntry(
            checksum="abc123",
            path=Path("a.txt"),
        )

        self.assertEqual(entry.checksum, "abc123")
        self.assertEqual(entry.path, Path("a.txt"))

    def test_render_manifest_entry(self):

        entry = manifest_model.ManifestEntry(
            checksum="deadbeef",
            path=Path("dir/file.txt"),
        )

        line = manifest_codec.render_manifest_entry(entry)

        self.assertEqual(
            line,
            "deadbeef  ./dir/file.txt",
        )

    def test_parse_manifest_line(self):

        entry = manifest_codec.parse_manifest_line(
            "abc123  ./dir/file.txt"
        )

        self.assertEqual(entry.checksum, "abc123")
        self.assertEqual(
            entry.path,
            Path("dir/file.txt"),
        )

    def test_parse_manifest_line_rejects_invalid(self):

        with self.assertRaises(ValueError):
            manifest_codec.parse_manifest_line(
                "invalid line"
            )

    def test_generate_manifest_entries(self):

        with pilotest.tmpdir() as td:
            root = td / "capture"
            root.mkdir()

            path = root / "a.txt"
            path.write_text("hello")

            entries = list(
                manifest_verify.generate_manifest_entries(root)
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

            entries = manifest_codec.load_manifest_entries(mf)

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
            manifest_model.ManifestEntry(
                checksum="aaa",
                path=Path("a.txt"),
            ),
            manifest_model.ManifestEntry(
                checksum="bbb",
                path=Path("b.txt"),
            ),
        ]

        lines = list(
            manifest_codec.render_manifest_lines(entries)
        )

        self.assertEqual(
            lines,
            [
                "aaa  ./a.txt",
                "bbb  ./b.txt",
            ]
        )


class TestManifestMutation(unittest.TestCase):

    def test_manifest_add_entry_mutation(self):

        mut = manifest_model.ManifestAddEntry(
            subset="pile",
            entry=manifest_model.ManifestEntry(
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

        mut = manifest_model.ManifestRemoveEntry(
            subset="pile",
            path=Path("in/a.txt"),
        )

        self.assertEqual(mut.subset, "pile")
        self.assertEqual(mut.path, Path("in/a.txt"))

    def test_apply_manifest_add_entry(self):

        entries = []

        mut = manifest_model.ManifestAddEntry(
            subset="pile",
            entry=manifest_model.ManifestEntry(
                checksum="abc",
                path=Path("in/a.txt"),
            )
        )

        out = manifest_mutation.apply_manifest_mutations(
            entries,
            [mut],
        )

        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].checksum, "abc")

    def test_apply_manifest_remove_entry(self):

        entries = [
            manifest_model.ManifestEntry(
                checksum="abc",
                path=Path("in/a.txt"),
            ),
            manifest_model.ManifestEntry(
                checksum="def",
                path=Path("in/b.txt"),
            ),
        ]

        mut = manifest_model.ManifestRemoveEntry(
            subset="pile",
            path=Path("in/a.txt"),
        )

        out = manifest_mutation.apply_manifest_mutations(
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
            manifest_model.ManifestEntry(
                checksum="old",
                path=Path("in/a.txt"),
            )
        ]

        mut = manifest_model.ManifestAddEntry(
            subset="pile",
            entry=manifest_model.ManifestEntry(
                checksum="new",
                path=Path("in/a.txt"),
            )
        )

        out = manifest_mutation.apply_manifest_mutations(
            entries,
            [mut],
        )

        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].checksum, "new")


class TestManifestStore(unittest.TestCase):
    def test_write_manifest_entries(self):

        with pilotest.make_tmp_context() as cx:

            out = cx.path / "test.manifest"

            entries = [
                manifest_model.ManifestEntry(
                    checksum="abc",
                    path=Path("in/a.txt"),
                )
            ]

            manifest_store.write_manifest_entries(
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

            manifest_store.write_manifest(cx, root, mfile)

            self.assertTrue(mfile.exists())

            text = mfile.read_text()

            self.assertIn("./a.txt", text)

    def test_write_manifest_entries_overwrites_existing(self):

        with pilotest.make_tmp_context() as cx:
            out = cx.path / "test.manifest"
            out.write_text("old data\n")
            entries = [
                manifest_model.ManifestEntry(
                    checksum="abc",
                    path=Path("in/a.txt"),
                )
            ]

            manifest_store.write_manifest_entries(cx, out, entries)
            text = out.read_text()
            self.assertEqual(text, "abc  ./in/a.txt\n")



class TestManifestPolicy(unittest.TestCase):

    def test_manifest_subset_root(self):
        cx = pilotest.make_context()

        self.assertEqual(
            manifest_policy.manifest_subset_root(
                cx,
                "pile",
            ),
            cx.pile_path,
        )

        self.assertEqual(
            manifest_policy.manifest_subset_root(
                cx,
                "collection",
            ),
            cx.static_path / "collection",
        )

        self.assertEqual(
            manifest_policy.manifest_subset_root(
                cx,
                "filing",
            ),
            cx.static_path / "filing",
        )

    def test_dataset_manifest_subset_pile(self):

        result = (
            manifest_policy.dataset_manifest_subset(
                "tank/a/pile"
            )
        )

        self.assertEqual(result, "pile")

    def test_dataset_manifest_subset_collection(self):

        result = (
            manifest_policy.dataset_manifest_subset(
                "tank/a/static/collection"
            )
        )

        self.assertEqual(result, "collection")

    def test_dataset_manifest_subset_filing(self):

        result = (
            manifest_policy.dataset_manifest_subset(
                "tank/a/static/filing/docs"
            )
        )

        self.assertEqual(result, "filing")

    def test_dataset_manifest_subset_unknown(self):

        result = (
            manifest_policy.dataset_manifest_subset(
                "tank/a/unknown"
            )
        )

        self.assertIsNone(result)

    def test_mutation_manifest_domains(self):

        muts = [
            mutation.MoveMutation(
                src=Path("/a"),
                dst=Path("/b"),
                dataset="tank/a/pile",
            ),
            mutation.CopyMutation(
                src=Path("/c"),
                dst=Path("/d"),
                dataset="tank/a/static/collection",
            ),
        ]

        result = mutation.mutation_manifest_domains(
            muts
        )

        self.assertEqual(
            result,
            {"pile", "collection"},
        )



class TestManifestUpdate(unittest.TestCase):

    def test_build_manifest_update_plan(self):
        cx = pilotest.make_context()

        plan = manifest_update.build_manifest_update_plan(
            cx,
            ["pile", "collection"],
        )

        self.assertEqual(
            [s.name for s in plan.subsets],
            ["pile", "collection"],
        )

    @patch("pilo.manifest_store.write_manifest")
    @patch("pilo.manifest_update.commit_manifest_if_changed")
    @patch("pilo.fs.ensure_parent_dir")
    def test_execute_manifest_update_plan(
        self,
        mock_dir,
        mock_commit,
        mock_write,
    ):
        cx = pilotest.make_context()

        plan = (
            manifest_update
            .build_manifest_update_plan(
                cx,
                ["pile"],
            )
        )

        manifest_update.execute_manifest_update_plan(
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

            manifest_store.write_manifest(
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

        manifest_update.commit_manifest_if_changed(
            cx,
            mfile,
            "test update",
        )

        mock_repo.assert_called_once()

        mock_commit.assert_called_once()
