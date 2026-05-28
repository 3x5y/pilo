import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from pilo.storage import cloud
import pilotest


class TestCloudManifest(pilotest.TestCase):

    def _make_entry(self, path="20260528/foo.zfs.manifest",
                    checksum="abc" * 20, size=100):
        return cloud.PackageEntry(path=path, checksum=checksum, size=size)

    def _make_package(self, archive="a.tar.zst", checksum="c", size=100,
                      created="now", entries=None):
        if entries is None:
            entries = (self._make_entry(),)
        return cloud.PackageManifest(
            archive=archive, checksum=checksum, size=size,
            created=created, entries=entries,
        )

    def _make_dict(self, version=1, fmt="tar.zst", recipient="",
                   checksum="c", size=100, created="now", package=None):
        if package is None:
            package = self._make_package()
        return {
            "version": version,
            "format": fmt,
            "recipient": recipient,
            "checksum": checksum,
            "size": size,
            "package": package.to_dict(),
            "created": created,
        }

    def test_construction(self):
        pkg = self._make_package()
        m = cloud.CloudManifest(
            version=1, format="tar.zst", recipient="",
            checksum="c", size=100,
            package=pkg, created="now",
        )
        self.assertEqual(m.version, 1)
        self.assertEqual(m.format, "tar.zst")
        self.assertEqual(m.package.archive, "a.tar.zst")

    def test_frozen(self):
        pkg = self._make_package()
        m = cloud.CloudManifest(
            version=1, format="f", recipient="r",
            checksum="c", size=1, package=pkg, created="now",
        )
        with self.assertRaises(AttributeError):
            m.version = 2

    def test_to_dict(self):
        pkg = self._make_package()
        m = cloud.CloudManifest(
            version=1, format="tar.zst", recipient="r",
            checksum="c", size=100, package=pkg, created="now",
        )
        d = m.to_dict()
        self.assertEqual(d["version"], 1)
        self.assertEqual(d["format"], "tar.zst")
        self.assertIn("package", d)
        self.assertEqual(d["package"]["archive"], "a.tar.zst")

    def test_from_dict(self):
        d = self._make_dict()
        m = cloud.CloudManifest.from_dict(d)
        self.assertEqual(m.version, 1)
        self.assertEqual(m.format, "tar.zst")
        self.assertEqual(m.package.archive, "a.tar.zst")
        self.assertEqual(len(m.package.entries), 1)

    def test_roundtrip(self):
        pkg = self._make_package()
        m1 = cloud.CloudManifest(
            version=1, format="tar.zst", recipient="r",
            checksum="c", size=100, package=pkg, created="now",
        )
        m2 = cloud.CloudManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)

    def test_from_dict_missing_field(self):
        with self.assertRaises(ValueError):
            cloud.CloudManifest.from_dict({"version": 1})

    def test_from_dict_version_not_int(self):
        d = self._make_dict(version="bad")
        with self.assertRaises(ValueError):
            cloud.CloudManifest.from_dict(d)

    def test_from_dict_size_not_int(self):
        d = self._make_dict(size="bad")
        with self.assertRaises(ValueError):
            cloud.CloudManifest.from_dict(d)

    def test_propagates_package_validation(self):
        d = self._make_dict()
        d["package"] = {"archive": "incomplete"}
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
            checksum="def" * 20,
            size=5000,
            created="2026-05-28T00:00:00+00:00",
            entries=(e,),
        )
        self.assertEqual(m.archive, "20260528.tar.zst")
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

    def test_returns_cloud_manifest(self):
        entry = cloud.PackageEntry(path="p", checksum="c", size=1)
        manifest = cloud.build_package_manifest(
            stamp="20260528",
            archive_checksum="abc" * 20,
            archive_size=5000,
            created="2026-05-28T00:00:00+00:00",
            entries=(entry,),
        )
        self.assertIsInstance(manifest, cloud.CloudManifest)

    def test_inner_package_manifest_fields(self):
        entry = cloud.PackageEntry(path="p", checksum="c", size=1)
        manifest = cloud.build_package_manifest(
            stamp="20260528",
            archive_checksum="abc" * 20,
            archive_size=5000,
            created="2026-05-28T00:00:00+00:00",
            entries=(entry,),
        )
        pkg = manifest.package
        self.assertEqual(pkg.archive, "20260528.tar.zst")
        self.assertEqual(pkg.checksum, "abc" * 20)
        self.assertEqual(pkg.size, 5000)
        self.assertEqual(pkg.created, "2026-05-28T00:00:00+00:00")
        self.assertEqual(len(pkg.entries), 1)
        self.assertEqual(pkg.entries[0].path, "p")

    def test_outer_cloud_manifest_fields(self):
        entry = cloud.PackageEntry(path="p", checksum="c", size=1)
        manifest = cloud.build_package_manifest(
            stamp="20260528",
            archive_checksum="abc" * 20,
            archive_size=5000,
            created="2026-05-28T00:00:00+00:00",
            entries=(entry,),
        )
        self.assertEqual(manifest.version, 1)
        self.assertEqual(manifest.format, "tar.zst")
        self.assertEqual(manifest.recipient, "")
        self.assertEqual(manifest.checksum, "abc" * 20)
        self.assertEqual(manifest.size, 5000)
        self.assertEqual(manifest.created, "2026-05-28T00:00:00+00:00")

    def test_checksums_match_between_layers(self):
        entry = cloud.PackageEntry(path="p", checksum="c", size=1)
        manifest = cloud.build_package_manifest(
            stamp="s", archive_checksum="chk", archive_size=1,
            created="now", entries=(entry,),
        )
        self.assertEqual(manifest.checksum, manifest.package.checksum)
        self.assertEqual(manifest.size, manifest.package.size)

    def test_multiple_entries(self):
        e1 = cloud.PackageEntry(path="a", checksum="c1", size=1)
        e2 = cloud.PackageEntry(path="b", checksum="c2", size=2)
        manifest = cloud.build_package_manifest(
            stamp="s", archive_checksum="chk", archive_size=10,
            created="now", entries=(e1, e2),
        )
        self.assertEqual(len(manifest.package.entries), 2)

    def test_empty_entries(self):
        manifest = cloud.build_package_manifest(
            stamp="s", archive_checksum="chk", archive_size=0,
            created="now", entries=(),
        )
        self.assertEqual(len(manifest.package.entries), 0)

    def test_roundtrip_serialization(self):
        entry = cloud.PackageEntry(path="p", checksum="c", size=1)
        m1 = cloud.build_package_manifest(
            stamp="20260528", archive_checksum="abc" * 20,
            archive_size=5000, created="now", entries=(entry,),
        )
        m2 = cloud.CloudManifest.from_dict(m1.to_dict())
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
            self.assertEqual(manifest.version, 1)
            self.assertEqual(
                manifest.package.archive, "20260528_120000.tar.zst"
            )
            self.assertEqual(len(manifest.package.entries), 1)
            self.assertEqual(
                manifest.package.entries[0].path,
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
        pkg = cloud.PackageManifest(
            archive="20260528.tar.zst",
            checksum="def" * 20,
            size=5000,
            created="2026-05-28T00:00:00+00:00",
            entries=(entry,),
        )
        return cloud.CloudManifest(
            version=1, format="tar.zst", recipient="",
            checksum="def" * 20, size=5000,
            package=pkg, created="2026-05-28T00:00:00+00:00",
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
            path.write_text('{"version": "bad"}')
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
