import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from pilo import fs
from pilo.storage import cloud
import pilotest


class TestCloudManifest(pilotest.TestCase):

    def _make_package(self, archive="a.tar.zst", format="tar.zst",
                      checksum="c", size=100, created="now", entries=None):
        if entries is None:
            entries = (cloud.PackageEntry(path="p", checksum="c", size=1),)
        return cloud.PackageManifest(
            archive=archive, format=format, checksum=checksum,
            size=size, created=created, entries=entries,
        )

    def test_construction(self):
        pkg = self._make_package()
        m = cloud.CloudManifest(version=1, package=pkg, created="now")
        self.assertEqual(m.version, 1)
        self.assertEqual(m.package.archive, "a.tar.zst")

    def test_frozen(self):
        pkg = self._make_package()
        m = cloud.CloudManifest(version=1, package=pkg, created="now")
        with self.assertRaises(AttributeError):
            m.version = 2

    def test_to_dict(self):
        pkg = self._make_package()
        m = cloud.CloudManifest(version=1, package=pkg, created="now")
        d = m.to_dict()
        self.assertEqual(d["version"], 1)
        self.assertIn("package", d)
        self.assertEqual(d["package"]["archive"], "a.tar.zst")

    def test_from_dict(self):
        pkg = self._make_package()
        d = {"version": 1, "package": pkg.to_dict(), "created": "now"}
        m = cloud.CloudManifest.from_dict(d)
        self.assertEqual(m.version, 1)
        self.assertEqual(m.package.archive, "a.tar.zst")
        self.assertEqual(len(m.package.entries), 1)

    def test_roundtrip(self):
        pkg = self._make_package()
        m1 = cloud.CloudManifest(version=1, package=pkg, created="now")
        m2 = cloud.CloudManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)

    def test_from_dict_missing_field(self):
        with self.assertRaises(ValueError):
            cloud.CloudManifest.from_dict({"version": 1})

    def test_from_dict_version_not_int(self):
        pkg = self._make_package()
        d = {"version": "bad", "package": pkg.to_dict(), "created": "now"}
        with self.assertRaises(ValueError):
            cloud.CloudManifest.from_dict(d)

    def test_propagates_package_validation(self):
        d = {"version": 1, "package": {"archive": "incomplete"},
             "created": "now"}
        with self.assertRaises(ValueError):
            cloud.CloudManifest.from_dict(d)


class TestPackageEntry(pilotest.TestCase):

    def test_construction(self):
        e = cloud.PackageEntry(
            path="20260528/foo.zfs.manifest",
            checksum="abc" * 20,
            size=4096,
        )
        self.assertEqual(e.path, "20260528/foo.zfs.manifest")
        self.assertEqual(e.checksum, "abc" * 20)
        self.assertEqual(e.size, 4096)

    def test_frozen(self):
        e = cloud.PackageEntry(path="p", checksum="c", size=1)
        with self.assertRaises(AttributeError):
            e.path = "other"

    def test_to_dict(self):
        e = cloud.PackageEntry(path="p", checksum="c", size=1)
        d = e.to_dict()
        self.assertEqual(d["path"], "p")
        self.assertEqual(d["checksum"], "c")
        self.assertEqual(d["size"], 1)

    def test_from_dict(self):
        d = {"path": "p", "checksum": "c", "size": 1}
        e = cloud.PackageEntry.from_dict(d)
        self.assertEqual(e.path, "p")
        self.assertEqual(e.checksum, "c")
        self.assertEqual(e.size, 1)

    def test_roundtrip(self):
        e1 = cloud.PackageEntry(path="p", checksum="c", size=1)
        e2 = cloud.PackageEntry.from_dict(e1.to_dict())
        self.assertEqual(e1, e2)

    def test_from_dict_missing_field(self):
        with self.assertRaises(ValueError):
            cloud.PackageEntry.from_dict({"path": "p", "checksum": "c"})

    def test_from_dict_size_not_int(self):
        with self.assertRaises(ValueError):
            cloud.PackageEntry.from_dict({
                "path": "p", "checksum": "c", "size": "not_int",
            })


class TestPackageManifest(pilotest.TestCase):

    def _make_entry(self, path="20260528/foo.zfs.manifest",
                    checksum="abc" * 20, size=100):
        return cloud.PackageEntry(path=path, checksum=checksum, size=size)

    def test_construction(self):
        e = self._make_entry()
        m = cloud.PackageManifest(
            archive="20260528.tar.zst",
            format="tar.zst",
            checksum="def" * 20,
            size=5000,
            created="2026-05-28T00:00:00+00:00",
            entries=(e,),
        )
        self.assertEqual(m.archive, "20260528.tar.zst")
        self.assertEqual(m.format, "tar.zst")
        self.assertEqual(m.size, 5000)
        self.assertEqual(len(m.entries), 1)

    def test_frozen(self):
        m = cloud.PackageManifest(
            archive="a", checksum="c", size=1, created="now", entries=(),
        )
        with self.assertRaises(AttributeError):
            m.archive = "other"

    def test_to_dict(self):
        e = self._make_entry()
        m = cloud.PackageManifest(
            archive="a.tar.zst", checksum="c", size=100,
            created="now", entries=(e,),
        )
        d = m.to_dict()
        self.assertEqual(d["archive"], "a.tar.zst")
        self.assertEqual(d["size"], 100)
        self.assertEqual(len(d["entries"]), 1)
        self.assertEqual(d["entries"][0]["path"], "20260528/foo.zfs.manifest")

    def test_from_dict(self):
        d = {
            "archive": "a.tar.zst",
            "checksum": "c",
            "size": 100,
            "created": "now",
            "entries": [
                {"path": "20260528/foo.zfs.manifest", "checksum": "c", "size": 10},
            ],
        }
        m = cloud.PackageManifest.from_dict(d)
        self.assertEqual(m.archive, "a.tar.zst")
        self.assertEqual(len(m.entries), 1)
        self.assertEqual(m.entries[0].path, "20260528/foo.zfs.manifest")

    def test_roundtrip(self):
        e = self._make_entry()
        m1 = cloud.PackageManifest(
            archive="a.tar.zst", checksum="c", size=100,
            created="now", entries=(e,),
        )
        m2 = cloud.PackageManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)

    def test_roundtrip_multiple_entries(self):
        e1 = self._make_entry(path="d1/f1.zfs.manifest", checksum="a", size=1)
        e2 = self._make_entry(path="d1/f2.zfs.manifest", checksum="b", size=2)
        m1 = cloud.PackageManifest(
            archive="a.tar.zst", checksum="c", size=100,
            created="now", entries=(e1, e2),
        )
        m2 = cloud.PackageManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)

    def test_from_dict_missing_field(self):
        with self.assertRaises(ValueError):
            cloud.PackageManifest.from_dict({"archive": "a"})

    def test_from_dict_size_not_int(self):
        with self.assertRaises(ValueError):
            cloud.PackageManifest.from_dict({
                "archive": "a", "checksum": "c", "size": "bad",
                "created": "now", "entries": [],
            })

    def test_from_dict_entries_not_list(self):
        with self.assertRaises(ValueError):
            cloud.PackageManifest.from_dict({
                "archive": "a", "checksum": "c", "size": 1,
                "created": "now", "entries": "not_a_list",
            })

    def test_rejects_zfs_stream_path(self):
        d = {
            "archive": "a.tar.zst", "checksum": "c", "size": 1,
            "created": "now",
            "entries": [
                {"path": "20260528/data.zfs", "checksum": "c", "size": 10},
            ],
        }
        with self.assertRaises(ValueError):
            cloud.PackageManifest.from_dict(d)

    def test_allows_zfs_manifest_path(self):
        d = {
            "archive": "a.tar.zst", "checksum": "c", "size": 1,
            "created": "now",
            "entries": [
                {"path": "20260528/data.zfs.manifest", "checksum": "c", "size": 10},
            ],
        }
        m = cloud.PackageManifest.from_dict(d)
        self.assertEqual(len(m.entries), 1)

    def test_rejects_absolute_path(self):
        d = {
            "archive": "a.tar.zst", "checksum": "c", "size": 1,
            "created": "now",
            "entries": [
                {"path": "/abs/path.zfs.manifest", "checksum": "c", "size": 10},
            ],
        }
        with self.assertRaises(ValueError):
            cloud.PackageManifest.from_dict(d)

    def test_rejects_absolute_path_in_non_zfs(self):
        d = {
            "archive": "a.tar.zst", "checksum": "c", "size": 1,
            "created": "now",
            "entries": [
                {"path": "/etc/passwd", "checksum": "c", "size": 10},
            ],
        }
        with self.assertRaises(ValueError):
            cloud.PackageManifest.from_dict(d)

    def test_propagates_entry_validation(self):
        d = {
            "archive": "a.tar.zst", "checksum": "c", "size": 1,
            "created": "now",
            "entries": [
                {"path": "p", "checksum": "c", "size": "not_int"},
            ],
        }
        with self.assertRaises(ValueError):
            cloud.PackageManifest.from_dict(d)


class TestValidatePackInput(pilotest.TestCase):

    def _valid_dir(self, td, stamp="20260528"):
        src = td / stamp
        src.mkdir()
        (src / f"{stamp}_010203_000000-reg.zfs").write_bytes(b"stream data")
        (src / f"{stamp}_010203_000000-reg.zfs.manifest").write_text(
            '{"stream":"s","snapshot":"s","source":"t","guid":"g",'
            '"checksum":"c","size":1,"created":"now"}'
        )
        return src

    def test_valid_directory(self):
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "out"
            dst.mkdir()
            cloud.validate_pack_input(src, dst, "20260528_120000")

    def test_valid_directory_creates_dst(self):
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "out"
            cloud.validate_pack_input(src, dst, "20260528_120000")

    def test_missing_src_raises(self):
        with pilotest.tmpdir() as td:
            src = td / "nonexistent"
            dst = td / "out"
            dst.mkdir()
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "20260528_120000")

    def test_src_is_file_raises(self):
        with pilotest.tmpdir() as td:
            src = td / "not_a_dir"
            src.write_text("")
            dst = td / "out"
            dst.mkdir()
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "not_a_dir")

    def test_invalid_stamp_format(self):
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "out"
            dst.mkdir()
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "bad-stamp")

    def test_output_exists_as_file_raises(self):
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "out"
            dst.write_text("i am a file")
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "20260528_120000")

    def test_output_archive_already_exists(self):
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "out"
            dst.mkdir()
            (dst / "20260528_120000.tar.zst").write_text("existing")
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "20260528_120000")

    def test_output_manifest_already_exists(self):
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "out"
            dst.mkdir()
            (dst / "20260528_120000.tar.zst.manifest").write_text("existing")
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "20260528_120000")

    def test_rejects_symlink(self):
        with pilotest.tmpdir() as td:
            src = td / "20260528"
            src.mkdir()
            target = td / "target"
            target.write_text("data")
            (src / "link.zfs").symlink_to(target)
            dst = td / "out"
            dst.mkdir()
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "20260528_120000")

    def test_rejects_nested_directory(self):
        with pilotest.tmpdir() as td:
            src = td / "20260528"
            src.mkdir()
            nested = src / "sub"
            nested.mkdir()
            (nested / "f.zfs").write_bytes(b"data")
            dst = td / "out"
            dst.mkdir()
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "20260528_120000")

    def test_rejects_hidden_file(self):
        with pilotest.tmpdir() as td:
            src = td / "20260528"
            src.mkdir()
            (src / ".hidden.zfs").write_bytes(b"data")
            dst = td / "out"
            dst.mkdir()
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "20260528_120000")

    def test_rejects_unexpected_file_type(self):
        with pilotest.tmpdir() as td:
            src = td / "20260528"
            src.mkdir()
            (src / "readme.txt").write_text("hello")
            dst = td / "out"
            dst.mkdir()
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "20260528_120000")

    def test_rejects_malformed_filename(self):
        with pilotest.tmpdir() as td:
            src = td / "20260528"
            src.mkdir()
            (src / "bad;chars.zfs").write_bytes(b"data")
            dst = td / "out"
            dst.mkdir()
            with self.assertRaises(ValueError):
                cloud.validate_pack_input(src, dst, "20260528_120000")


class TestBuildPackageManifest(pilotest.TestCase):

    def test_returns_package_manifest(self):
        entry = cloud.PackageEntry(path="p", checksum="c", size=1)
        manifest = cloud.build_package_manifest(
            stamp="20260528",
            archive_checksum="abc" * 20,
            archive_size=5000,
            created="2026-05-28T00:00:00+00:00",
            entries=(entry,),
        )
        self.assertIsInstance(manifest, cloud.PackageManifest)

    def test_fields(self):
        entry = cloud.PackageEntry(path="p", checksum="c", size=1)
        manifest = cloud.build_package_manifest(
            stamp="20260528",
            archive_checksum="abc" * 20,
            archive_size=5000,
            created="2026-05-28T00:00:00+00:00",
            entries=(entry,),
        )
        self.assertEqual(manifest.archive, "20260528.tar.zst")
        self.assertEqual(manifest.format, "tar.zst")
        self.assertEqual(manifest.checksum, "abc" * 20)
        self.assertEqual(manifest.size, 5000)
        self.assertEqual(manifest.created, "2026-05-28T00:00:00+00:00")
        self.assertEqual(len(manifest.entries), 1)
        self.assertEqual(manifest.entries[0].path, "p")

    def test_multiple_entries(self):
        e1 = cloud.PackageEntry(path="a", checksum="c1", size=1)
        e2 = cloud.PackageEntry(path="b", checksum="c2", size=2)
        manifest = cloud.build_package_manifest(
            stamp="s", archive_checksum="chk", archive_size=10,
            created="now", entries=(e1, e2),
        )
        self.assertEqual(len(manifest.entries), 2)

    def test_empty_entries(self):
        manifest = cloud.build_package_manifest(
            stamp="s", archive_checksum="chk", archive_size=0,
            created="now", entries=(),
        )
        self.assertEqual(len(manifest.entries), 0)

    def test_roundtrip_serialization(self):
        entry = cloud.PackageEntry(path="p", checksum="c", size=1)
        m1 = cloud.build_package_manifest(
            stamp="20260528", archive_checksum="abc" * 20,
            archive_size=5000, created="now", entries=(entry,),
        )
        m2 = cloud.PackageManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)


class TestPackStreamDay(pilotest.TestCase):

    def _valid_dir(self, td, stamp="20260528"):
        src = td / stamp
        src.mkdir()
        (src / f"{stamp}_010203_000000-reg.zfs").write_bytes(b"stream data")
        (src / f"{stamp}_010203_000000-reg.zfs.manifest").write_text(
            '{"stream":"s","snapshot":"s","source":"t","guid":"g",'
            '"checksum":"c","size":1,"created":"now"}'
        )
        return src

    def _mock_tar(self, args, **kw):
        idx = args.index("-cf")
        archive_path = args[idx + 1]
        Path(archive_path).write_bytes(b"fake tar archive")

    def test_successful_pack(self):
        fixed_dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "out"
            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "path")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                result = cloud.pack_stream_day(src, dst)

            expected_archive = dst / "20260528_120000.tar.zst"
            self.assertEqual(result, expected_archive)
            self.assertTrue(expected_archive.exists())
            self.assertTrue(
                (dst / "20260528_120000.tar.zst.manifest").exists()
            )

    def test_returns_archive_path(self):
        fixed_dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "out"
            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "path")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                result = cloud.pack_stream_day(src, dst)
            self.assertIsInstance(result, Path)
            self.assertEqual(result.name, "20260528_120000.tar.zst")

    def test_creates_dst_dir(self):
        fixed_dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "nonexistent/out"
            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "path")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                cloud.pack_stream_day(src, dst)
            self.assertTrue(dst.is_dir())

    def test_manifest_is_valid(self):
        fixed_dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "out"
            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "path")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                cloud.pack_stream_day(src, dst)

            manifest = cloud.load_package_manifest(
                dst / "20260528_120000.tar.zst.manifest"
            )
            self.assertEqual(manifest.archive, "20260528_120000.tar.zst")
            self.assertEqual(manifest.format, "tar.zst")
            self.assertEqual(len(manifest.entries), 1)
            self.assertEqual(
                manifest.entries[0].path,
                "20260528_010203_000000-reg.zfs.manifest",
            )

    def test_no_manifests_raises(self):
        with pilotest.tmpdir() as td:
            src = td / "20260528"
            src.mkdir()
            (src / "orphan.zfs").write_bytes(b"data")
            dst = td / "out"
            dst.mkdir()
            with self.assertRaises(ValueError):
                cloud.pack_stream_day(src, dst)

    def test_stream_verification_failure_raises(self):
        fixed_dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            src = self._valid_dir(td)
            dst = td / "out"
            dst.mkdir()
            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("MISMATCH", "bad path")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                with self.assertRaises(ValueError):
                    cloud.pack_stream_day(src, dst)


class TestPackageManifestIO(pilotest.TestCase):

    def _make_manifest(self):
        entry = cloud.PackageEntry(
            path="20260528/foo.zfs.manifest",
            checksum="abc" * 20, size=100,
        )
        return cloud.PackageManifest(
            archive="20260528.tar.zst",
            format="tar.zst",
            checksum="def" * 20,
            size=5000,
            created="2026-05-28T00:00:00+00:00",
            entries=(entry,),
        )

    def test_write_then_load_roundtrip(self):
        m1 = self._make_manifest()
        with pilotest.tmpdir() as td:
            path = td / "manifest.json"
            cloud.write_package_manifest(m1, path)
            m2 = cloud.load_package_manifest(path)
        self.assertEqual(m1, m2)

    def test_output_is_newline_terminated(self):
        m = self._make_manifest()
        with pilotest.tmpdir() as td:
            path = td / "manifest.json"
            cloud.write_package_manifest(m, path)
            text = path.read_text()
        self.assertTrue(text.endswith("\n"))

    def test_output_is_deterministic(self):
        m = self._make_manifest()
        with pilotest.tmpdir() as td:
            path1 = td / "m1.json"
            path2 = td / "m2.json"
            cloud.write_package_manifest(m, path1)
            cloud.write_package_manifest(m, path2)
            self.assertEqual(path1.read_bytes(), path2.read_bytes())

    def test_load_malformed_json_raises(self):
        with pilotest.tmpdir() as td:
            path = td / "bad.json"
            path.write_text("not json")
            with self.assertRaises(Exception):
                cloud.load_package_manifest(path)

    def test_load_missing_file_raises(self):
        from pathlib import Path
        with self.assertRaises(FileNotFoundError):
            cloud.load_package_manifest(Path("/tmp/nonexistent.manifest"))

    def test_load_invalid_schema_raises(self):
        with pilotest.tmpdir() as td:
            path = td / "bad.json"
            path.write_text('{"archive": "bad"}')
            with self.assertRaises(ValueError):
                cloud.load_package_manifest(path)


class TestStorageCloudPackCommand(pilotest.TestCase):

    def _mock_tar(self, args, **kw):
        idx = args.index("-cf")
        Path(args[idx + 1]).write_bytes(b"fake archive")

    def test_valid_invocation(self):
        mod = pilotest.import_command("storage-cloud-pack")
        fixed_dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            src = td / "20260528"
            src.mkdir()
            (src / "20260528_010203_000000-reg.zfs").write_bytes(b"s")
            (src / "20260528_010203_000000-reg.zfs.manifest").write_text(
                '{"stream":"s","snapshot":"s","source":"t","guid":"g",'
                '"checksum":"c","size":1,"created":"now"}'
            )
            dst = td / "out"
            dst.mkdir()
            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-pack", str(src), str(dst),
                ]),
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "path")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                with pilotest.suppress_stdout():
                    mod.main()

            self.assertTrue((dst / "20260528_120000.tar.zst").exists())

    def test_missing_args_exits(self):
        mod = pilotest.import_command("storage-cloud-pack")
        with (
            patch("sys.argv", ["pilo-storage-cloud-pack"]),
            patch("sys.stderr"),
        ):
            with self.assertRaises(SystemExit) as cm:
                mod.main()
        self.assertEqual(cm.exception.code, 1)


class TestEncryptedArchive(pilotest.TestCase):

    def test_construction(self):
        e = cloud.EncryptedArchive(
            recipient="age1key",
            name="20260528_120000.tar.zst.age",
            checksum="abc" * 20,
            size=5000,
        )
        self.assertEqual(e.format, "age")
        self.assertEqual(e.recipient, "age1key")
        self.assertEqual(e.name, "20260528_120000.tar.zst.age")
        self.assertEqual(e.checksum, "abc" * 20)
        self.assertEqual(e.size, 5000)

    def test_frozen(self):
        e = cloud.EncryptedArchive(recipient="r", name="n",
                                   checksum="c", size=1)
        with self.assertRaises(AttributeError):
            e.name = "other"

    def test_to_dict(self):
        e = cloud.EncryptedArchive(recipient="r", name="n",
                                   checksum="c", size=1)
        d = e.to_dict()
        self.assertEqual(d["format"], "age")
        self.assertEqual(d["recipient"], "r")
        self.assertEqual(d["name"], "n")
        self.assertEqual(d["checksum"], "c")
        self.assertEqual(d["size"], 1)

    def test_from_dict(self):
        d = {"format": "age", "recipient": "r", "name": "n",
             "checksum": "c", "size": 1}
        e = cloud.EncryptedArchive.from_dict(d)
        self.assertEqual(e.format, "age")
        self.assertEqual(e.recipient, "r")
        self.assertEqual(e.name, "n")
        self.assertEqual(e.checksum, "c")
        self.assertEqual(e.size, 1)

    def test_roundtrip(self):
        e1 = cloud.EncryptedArchive(recipient="r", name="n",
                                    checksum="c", size=1)
        e2 = cloud.EncryptedArchive.from_dict(e1.to_dict())
        self.assertEqual(e1, e2)

    def test_from_dict_missing_field(self):
        with self.assertRaises(ValueError):
            cloud.EncryptedArchive.from_dict({"name": "n", "checksum": "c"})

    def test_from_dict_size_not_int(self):
        with self.assertRaises(ValueError):
            cloud.EncryptedArchive.from_dict({
                "recipient": "r", "name": "n",
                "checksum": "c", "size": "not_int",
            })


class TestCloudManifestEncryptedArchive(pilotest.TestCase):

    def _make_package(self):
        return cloud.PackageManifest(
            archive="20260528_120000.tar.zst",
            format="tar.zst",
            checksum="def" * 20, size=5000,
            created="now",
            entries=(cloud.PackageEntry(
                path="20260528/foo.zfs.manifest",
                checksum="abc" * 20, size=100,
            ),),
        )

    def _make_encrypted(self):
        return cloud.EncryptedArchive(
            recipient="age1...",
            name="20260528_120000.tar.zst.age",
            checksum="ghi" * 20, size=3000,
        )

    def test_roundtrip_with_encrypted_archive(self):
        enc = self._make_encrypted()
        pkg = self._make_package()
        m1 = cloud.CloudManifest(
            version=1, package=pkg, created="now",
            encrypted_archive=enc,
        )
        m2 = cloud.CloudManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)
        self.assertIsNotNone(m2.encrypted_archive)
        self.assertEqual(m2.encrypted_archive.name, enc.name)

    def test_roundtrip_without_encrypted_archive(self):
        pkg = self._make_package()
        m1 = cloud.CloudManifest(
            version=1, package=pkg, created="now",
        )
        m2 = cloud.CloudManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)
        self.assertIsNone(m2.encrypted_archive)

    def test_to_dict_omits_encrypted_when_none(self):
        pkg = self._make_package()
        m = cloud.CloudManifest(
            version=1, package=pkg, created="now",
        )
        d = m.to_dict()
        self.assertNotIn("encrypted_archive", d)

    def test_from_dict_handles_encrypted_archive_field(self):
        enc = self._make_encrypted()
        pkg = self._make_package()
        d = {
            "version": 1, "package": pkg.to_dict(), "created": "now",
            "encrypted_archive": enc.to_dict(),
        }
        m = cloud.CloudManifest.from_dict(d)
        self.assertIsNotNone(m.encrypted_archive)

    def test_backward_compat_no_encrypted_archive(self):
        pkg = self._make_package()
        d = {
            "version": 1, "package": pkg.to_dict(), "created": "now",
        }
        m = cloud.CloudManifest.from_dict(d)
        self.assertIsNone(m.encrypted_archive)

    def test_encrypted_archive_validation_propagates(self):
        pkg = self._make_package()
        enc = {"recipient": "r", "name": "bad", "checksum": "c",
               "size": "not_int"}
        d = {
            "version": 1, "package": pkg.to_dict(), "created": "now",
            "encrypted_archive": enc,
        }
        with self.assertRaises(ValueError):
            cloud.CloudManifest.from_dict(d)


class TestEncryptArchive(pilotest.TestCase):

    def _mock_age(self, args, **kw):
        idx = args.index("-o")
        output = Path(args[idx + 1])
        output.write_bytes(b"encrypted content")

    def _make_archive_and_manifest(self, td, stamp="20260528_120000",
                                   checksum=None):
        archive = td / f"{stamp}.tar.zst"
        content = checksum.encode() if checksum else b"original content"
        archive.write_bytes(content)
        entry = cloud.PackageEntry(
            path=f"{stamp[:8]}/foo.zfs.manifest",
            checksum="abc" * 20, size=100,
        )
        pkg = cloud.PackageManifest(
            archive=f"{stamp}.tar.zst",
            format="tar.zst",
            checksum=fs.hash_file1(archive),
            size=archive.stat().st_size,
            created="now",
            entries=(entry,),
        )
        manifest_path = td / f"{stamp}.tar.zst.manifest"
        cloud.write_package_manifest(pkg, manifest_path)
        return archive, manifest_path

    def test_successful_encrypt(self):
        with pilotest.tmpdir() as td:
            archive, _ = self._make_archive_and_manifest(td)
            dst = td / "out"
            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=self._mock_age):
                enc_path, cloud_manifest = cloud.encrypt_archive(
                    archive, dst, "age1test",
                )

            self.assertEqual(
                enc_path.name, "20260528_120000.tar.zst.age"
            )
            self.assertTrue(enc_path.exists())
            self.assertIsInstance(cloud_manifest, cloud.CloudManifest)
            enc = cloud_manifest.encrypted_archive
            self.assertIsNotNone(enc)
            self.assertEqual(enc.name, "20260528_120000.tar.zst.age")
            self.assertEqual(enc.recipient, "age1test")
            self.assertEqual(enc.format, "age")
            self.assertIsInstance(enc.size, int)

    def test_returns_encrypted_path(self):
        with pilotest.tmpdir() as td:
            archive, _ = self._make_archive_and_manifest(td)
            dst = td / "out"
            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=self._mock_age):
                enc_path, _ = cloud.encrypt_archive(archive, dst, "rec")
            self.assertIsInstance(enc_path, Path)
            self.assertTrue(str(enc_path).endswith(".tar.zst.age"))

    def test_creates_dst_dir(self):
        with pilotest.tmpdir() as td:
            archive, _ = self._make_archive_and_manifest(td)
            dst = td / "deep/nested/out"
            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=self._mock_age):
                cloud.encrypt_archive(archive, dst, "rec")
            self.assertTrue(dst.is_dir())

    def test_with_identity_roundtrip(self):
        with pilotest.tmpdir() as td:
            archive, _ = self._make_archive_and_manifest(td)
            dst = td / "out"

            def mock_age(args, **kw):
                idx = args.index("-o")
                output = Path(args[idx + 1])
                if "-d" in args:
                    output.write_bytes(archive.read_bytes())
                else:
                    output.write_bytes(b"encrypted content")

            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=mock_age):
                enc_path, enc_archive = cloud.encrypt_archive(
                    archive, dst, "rec", identity="keyfile",
                )

            self.assertTrue(enc_path.exists())

    def test_identity_decrypt_mismatch_raises(self):
        with pilotest.tmpdir() as td:
            archive, _ = self._make_archive_and_manifest(td)
            dst = td / "out"

            def mock_age(args, **kw):
                idx = args.index("-o")
                output = Path(args[idx + 1])
                if "-d" in args:
                    output.write_bytes(b"different content")
                else:
                    output.write_bytes(b"encrypted content")

            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=mock_age),
            ):
                with self.assertRaises(ValueError):
                    cloud.encrypt_archive(
                        archive, dst, "rec", identity="keyfile",
                    )

    def test_archive_not_file_raises(self):
        with pilotest.tmpdir() as td:
            archive = td / "nonexistent.tar.zst"
            dst = td / "out"
            with self.assertRaises(ValueError):
                cloud.encrypt_archive(archive, dst, "rec")

    def test_empty_recipient_raises(self):
        with pilotest.tmpdir() as td:
            archive = td / "test.tar.zst"
            archive.write_text("data")
            dst = td / "out"
            with self.assertRaises(ValueError):
                cloud.encrypt_archive(archive, dst, "")

    def test_wrong_extension_raises(self):
        with pilotest.tmpdir() as td:
            archive = td / "test.txt"
            archive.write_text("data")
            dst = td / "out"
            with self.assertRaises(ValueError):
                cloud.encrypt_archive(archive, dst, "rec")

    def test_missing_manifest_raises(self):
        with pilotest.tmpdir() as td:
            archive = td / "20260528_120000.tar.zst"
            archive.write_bytes(b"data")
            dst = td / "out"
            with self.assertRaises(ValueError):
                cloud.encrypt_archive(archive, dst, "rec")

    def test_checksum_mismatch_raises(self):
        with pilotest.tmpdir() as td:
            archive, _ = self._make_archive_and_manifest(
                td, checksum="real content",
            )
            archive.write_bytes(b"tampered content")
            dst = td / "out"
            with self.assertRaises(ValueError):
                cloud.encrypt_archive(archive, dst, "rec")

    def test_output_already_exists_raises(self):
        with pilotest.tmpdir() as td:
            archive, _ = self._make_archive_and_manifest(td)
            dst = td / "out"
            dst.mkdir()
            (dst / "20260528_120000.tar.zst.age").write_text("existing")
            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=self._mock_age):
                with self.assertRaises(ValueError):
                    cloud.encrypt_archive(archive, dst, "rec")

    def test_age_manifest_already_exists_raises(self):
        with pilotest.tmpdir() as td:
            archive, _ = self._make_archive_and_manifest(td)
            dst = td / "out"
            dst.mkdir()
            (dst / "20260528_120000.tar.zst.age.manifest").write_text(
                "existing"
            )
            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=self._mock_age):
                with self.assertRaises(ValueError):
                    cloud.encrypt_archive(archive, dst, "rec")


class TestStorageCloudEncryptCommand(pilotest.TestCase):

    def _setup_artefacts(self, td, stamp="20260528_120000"):
        archive = td / f"{stamp}.tar.zst"
        content = b"archive content"
        archive.write_bytes(content)
        entry = cloud.PackageEntry(
            path="20260528/foo.zfs.manifest",
            checksum="abc" * 20, size=100,
        )
        pkg = cloud.PackageManifest(
            archive=f"{stamp}.tar.zst",
            format="tar.zst",
            checksum=fs.hash_file1(archive),
            size=archive.stat().st_size,
            created="now", entries=(entry,),
        )
        cloud.write_package_manifest(
            pkg, td / f"{stamp}.tar.zst.manifest",
        )
        return archive, content

    def test_valid_invocation(self):
        mod = pilotest.import_command("storage-cloud-encrypt")
        with pilotest.tmpdir() as td:
            archive, _ = self._setup_artefacts(td)
            dst = td / "out"
            dst.mkdir()
            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-encrypt",
                    "age1recipient", str(archive), str(dst),
                ]),
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=lambda args, **kw: Path(
                          args[args.index("-o") + 1]
                      ).write_bytes(b"encrypted")),
            ):
                with pilotest.suppress_stdout():
                    mod.main()

            self.assertTrue(
                (dst / "20260528_120000.tar.zst.age").exists()
            )
            self.assertTrue(
                (dst / "20260528_120000.tar.zst.age.manifest").exists()
            )

    def test_manifest_has_encrypted_metadata(self):
        mod = pilotest.import_command("storage-cloud-encrypt")
        with pilotest.tmpdir() as td:
            archive, _ = self._setup_artefacts(td)
            dst = td / "out"
            dst.mkdir()
            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-encrypt",
                    "age1key", str(archive), str(dst),
                ]),
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=lambda args, **kw: Path(
                          args[args.index("-o") + 1]
                      ).write_bytes(b"encrypted")),
            ):
                with pilotest.suppress_stdout():
                    mod.main()

            age_manifest = cloud.load_cloud_manifest(
                dst / "20260528_120000.tar.zst.age.manifest"
            )
            self.assertIsNotNone(age_manifest.encrypted_archive)
            self.assertEqual(
                age_manifest.encrypted_archive.recipient, "age1key"
            )
            self.assertEqual(
                age_manifest.encrypted_archive.name,
                "20260528_120000.tar.zst.age",
            )

    def test_missing_args_exits(self):
        mod = pilotest.import_command("storage-cloud-encrypt")
        with (
            patch("sys.argv", ["pilo-storage-cloud-encrypt"]),
            patch("sys.stderr"),
        ):
            with self.assertRaises(SystemExit) as cm:
                mod.main()
        self.assertEqual(cm.exception.code, 1)

    def test_identity_flag(self):
        mod = pilotest.import_command("storage-cloud-encrypt")
        with pilotest.tmpdir() as td:
            archive, content = self._setup_artefacts(td)
            dst = td / "out"
            dst.mkdir()
            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-encrypt",
                    "--identity", "/tmp/key",
                    "age1key", str(archive), str(dst),
                ]),
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=lambda args, **kw: Path(
                          args[args.index("-o") + 1]
                      ).write_bytes(
                          content if "-d" in args else b"encrypted"
                      )),
            ):
                with pilotest.suppress_stdout():
                    mod.main()

            self.assertTrue(
                (dst / "20260528_120000.tar.zst.age").exists()
            )
