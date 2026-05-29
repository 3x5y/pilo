import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from subprocess import CalledProcessError

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
                result = cloud._legacy_pack_stream_day(src, dst)

            expected_archive = dst / "20260528_120000.tar.zst"
            self.assertEqual(result, expected_archive)
            self.assertTrue(expected_archive.exists())
            self.assertTrue(
                (dst / "20260528_120000.tar.zst.manifest").exists()
            )


class TestVerifyDecryptedArchive(pilotest.TestCase):

    def test_verifies_matching_content(self):
        with pilotest.tmpdir() as td:
            path = td / "test.tar.zst"
            path.write_bytes(b"content")
            manifest = cloud.PackageManifest(
                archive="test.tar.zst",
                checksum=fs.hash_file1(path),
                size=7,
                created="now",
            )
            cloud.verify_decrypted_archive(path, manifest)

    def test_checksum_mismatch_raises(self):
        with pilotest.tmpdir() as td:
            path = td / "test.tar.zst"
            path.write_bytes(b"content")
            manifest = cloud.PackageManifest(
                archive="test.tar.zst",
                checksum="wrongchecksum",
                size=7,
                created="now",
            )
            with self.assertRaises(ValueError):
                cloud.verify_decrypted_archive(path, manifest)

    def test_size_mismatch_raises(self):
        with pilotest.tmpdir() as td:
            path = td / "test.tar.zst"
            path.write_bytes(b"content")
            manifest = cloud.PackageManifest(
                archive="test.tar.zst",
                checksum=fs.hash_file1(path),
                size=999,
                created="now",
            )
            with self.assertRaises(ValueError):
                cloud.verify_decrypted_archive(path, manifest)


class TestDecryptArchive(pilotest.TestCase):

    ORIGINAL_CONTENT = b"original tar archive content"

    def _make_encrypted_artefacts(self, td, stamp="20260528_120000"):
        archive_path = td / f"{stamp}.tar.zst.age"
        orig = td / "__orig"
        orig.write_bytes(self.ORIGINAL_CONTENT)
        orig_checksum = fs.hash_file1(orig)
        archive_path.write_bytes(b"encrypted version")
        entry = cloud.PackageEntry(
            path="20260528/foo.zfs.manifest",
            checksum="abc" * 20, size=100,
        )
        pkg = cloud.PackageManifest(
            archive=f"{stamp}.tar.zst",
            format="tar.zst",
            checksum=orig_checksum,
            size=len(self.ORIGINAL_CONTENT),
            created="now", entries=(entry,),
        )
        enc = cloud.EncryptedArchive(
            recipient="age1key",
            name=f"{stamp}.tar.zst.age",
            checksum=fs.hash_file1(archive_path),
            size=archive_path.stat().st_size,
        )
        cm = cloud.CloudManifest(
            version=1, package=pkg, created="now",
            encrypted_archive=enc,
        )
        manifest_path = td / f"{stamp}.tar.zst.age.manifest"
        cloud.write_cloud_manifest(cm, manifest_path)
        return archive_path, manifest_path

    def _mock_age_write_original(self, args, **kw):
        idx = args.index("-o")
        Path(args[idx + 1]).write_bytes(self.ORIGINAL_CONTENT)

    def test_decrypts_successfully(self):
        with pilotest.tmpdir() as td:
            archive_path, _ = self._make_encrypted_artefacts(td)
            identity = td / "key"
            identity.write_text("identity key")
            dst = td / "out"
            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=self._mock_age_write_original):
                result = cloud.decrypt_archive(
                    archive_path, dst, identity,
                )

            expected = dst / "20260528_120000.tar.zst"
            self.assertEqual(result, expected)
            self.assertTrue(expected.exists())
            self.assertEqual(expected.read_bytes(), self.ORIGINAL_CONTENT)

    def test_creates_dst_dir(self):
        with pilotest.tmpdir() as td:
            archive_path, _ = self._make_encrypted_artefacts(td)
            identity = td / "key"
            identity.write_text("identity key")
            dst = td / "deep/nested/out"
            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=self._mock_age_write_original):
                cloud.decrypt_archive(archive_path, dst, identity)
            self.assertTrue(dst.is_dir())

    def test_wrong_key_raises(self):
        with pilotest.tmpdir() as td:
            archive_path, _ = self._make_encrypted_artefacts(td)
            identity = td / "key"
            identity.write_text("identity key")
            dst = td / "out"
            with patch(
                "pilo.storage.cloud.subprocess.run",
                side_effect=CalledProcessError(1, "age"),
            ):
                with self.assertRaises(ValueError):
                    cloud.decrypt_archive(archive_path, dst, identity)

    def test_corrupt_encrypted_archive_raises(self):
        with pilotest.tmpdir() as td:
            archive_path, _ = self._make_encrypted_artefacts(td)
            archive_path.write_bytes(b"tampered content")
            identity = td / "key"
            identity.write_text("identity key")
            dst = td / "out"
            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=self._mock_age_write_original):
                with self.assertRaises(ValueError):
                    cloud.decrypt_archive(archive_path, dst, identity)

    def test_modified_manifest_raises(self):
        with pilotest.tmpdir() as td:
            archive_path, manifest_path = self._make_encrypted_artefacts(td)
            manifest_path.write_text('{"corrupted": true}')
            identity = td / "key"
            identity.write_text("identity key")
            dst = td / "out"
            with self.assertRaises(ValueError):
                cloud.decrypt_archive(archive_path, dst, identity)

    def test_checksum_mismatch_after_decrypt_raises(self):
        with pilotest.tmpdir() as td:
            archive_path, _ = self._make_encrypted_artefacts(td)
            identity = td / "key"
            identity.write_text("identity key")
            dst = td / "out"

            def mock_wrong_content(args, **kw):
                idx = args.index("-o")
                Path(args[idx + 1]).write_bytes(
                    b"different decrypted content"
                )

            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=mock_wrong_content):
                with self.assertRaises(ValueError):
                    cloud.decrypt_archive(archive_path, dst, identity)

    def test_missing_encrypted_archive_raises(self):
        with pilotest.tmpdir() as td:
            archive_path = td / "nonexistent.tar.zst.age"
            identity = td / "key"
            identity.write_text("key")
            dst = td / "out"
            with self.assertRaises(ValueError):
                cloud.decrypt_archive(archive_path, dst, identity)

    def test_missing_manifest_raises(self):
        with pilotest.tmpdir() as td:
            archive_path = td / "test.tar.zst.age"
            archive_path.write_bytes(b"data")
            identity = td / "key"
            identity.write_text("key")
            dst = td / "out"
            with self.assertRaises(ValueError):
                cloud.decrypt_archive(archive_path, dst, identity)

    def test_missing_identity_raises(self):
        with pilotest.tmpdir() as td:
            archive_path = td / "test.tar.zst.age"
            archive_path.write_bytes(b"data")
            manifest_path = td / "test.tar.zst.age.manifest"
            manifest_path.write_text('{"version":1}')
            identity = td / "nonexistent.key"
            dst = td / "out"
            with self.assertRaises(ValueError):
                cloud.decrypt_archive(archive_path, dst, identity)

    def test_output_already_exists_raises(self):
        with pilotest.tmpdir() as td:
            archive_path, _ = self._make_encrypted_artefacts(td)
            identity = td / "key"
            identity.write_text("identity key")
            dst = td / "out"
            dst.mkdir()
            (dst / "20260528_120000.tar.zst").write_text("existing")
            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=self._mock_age_write_original):
                with self.assertRaises(ValueError):
                    cloud.decrypt_archive(archive_path, dst, identity)

    def test_wrong_extension_raises(self):
        with pilotest.tmpdir() as td:
            archive_path = td / "test.txt"
            archive_path.write_text("data")
            identity = td / "key"
            identity.write_text("key")
            dst = td / "out"
            with self.assertRaises(ValueError):
                cloud.decrypt_archive(archive_path, dst, identity)


class TestStorageCloudDecryptCommand(pilotest.TestCase):

    ORIGINAL_CONTENT = b"original tar archive content"

    def _setup_artefacts(self, td, stamp="20260528_120000"):
        archive_path = td / f"{stamp}.tar.zst.age"
        orig = td / "__orig"
        orig.write_bytes(self.ORIGINAL_CONTENT)
        orig_checksum = fs.hash_file1(orig)
        archive_path.write_bytes(b"encrypted version")
        entry = cloud.PackageEntry(
            path="20260528/foo.zfs.manifest",
            checksum="abc" * 20, size=100,
        )
        pkg = cloud.PackageManifest(
            archive=f"{stamp}.tar.zst",
            format="tar.zst",
            checksum=orig_checksum,
            size=len(self.ORIGINAL_CONTENT),
            created="now", entries=(entry,),
        )
        enc = cloud.EncryptedArchive(
            recipient="age1key",
            name=f"{stamp}.tar.zst.age",
            checksum=fs.hash_file1(archive_path),
            size=archive_path.stat().st_size,
        )
        cm = cloud.CloudManifest(
            version=1, package=pkg, created="now",
            encrypted_archive=enc,
        )
        manifest_path = td / f"{stamp}.tar.zst.age.manifest"
        cloud.write_cloud_manifest(cm, manifest_path)
        identity = td / "key"
        identity.write_text("identity key")
        return archive_path, identity

    def test_valid_invocation(self):
        mod = pilotest.import_command("storage-cloud-decrypt")
        with pilotest.tmpdir() as td:
            archive_path, identity = self._setup_artefacts(td)
            dst = td / "out"
            dst.mkdir()
            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-decrypt",
                    str(identity), str(archive_path), str(dst),
                ]),
                patch(
                    "pilo.storage.cloud.subprocess.run",
                    side_effect=lambda args, **kw: Path(
                        args[args.index("-o") + 1]
                    ).write_bytes(self.ORIGINAL_CONTENT),
                ),
            ):
                with pilotest.suppress_stdout():
                    mod.main()

            self.assertTrue(
                (dst / "20260528_120000.tar.zst").exists()
            )

    def test_missing_args_exits(self):
        mod = pilotest.import_command("storage-cloud-decrypt")
        with (
            patch("sys.argv", ["pilo-storage-cloud-decrypt"]),
            patch("sys.stderr"),
        ):
            with self.assertRaises(SystemExit) as cm:
                mod.main()
        self.assertEqual(cm.exception.code, 1)


class TestStorageCloudSignCommand(pilotest.TestCase):

    def _setup_artefacts(self, td, stamp="20260528_120000"):
        archive_path = td / f"{stamp}.tar.zst.age"
        archive_path.write_bytes(b"encrypted data")
        entry = cloud.PackageEntry(
            path="20260528/foo.zfs.manifest",
            checksum="abc" * 20, size=100,
        )
        pkg = cloud.PackageManifest(
            archive=f"{stamp}.tar.zst",
            format="tar.zst",
            checksum="def" * 20, size=200,
            created="now", entries=(entry,),
        )
        enc = cloud.EncryptedArchive(
            recipient="age1key",
            name=f"{stamp}.tar.zst.age",
            checksum=fs.hash_file1(archive_path),
            size=archive_path.stat().st_size,
        )
        cm = cloud.CloudManifest(
            version=1, package=pkg, created="now",
            encrypted_archive=enc,
        )
        manifest_path = td / f"{stamp}.tar.zst.age.manifest"
        cloud.write_cloud_manifest(cm, manifest_path)
        keyfile = td / "minisign.key"
        keyfile.write_text("key data")
        return manifest_path, keyfile

    def test_valid_invocation(self):
        mod = pilotest.import_command("storage-cloud-sign-manifest")
        with pilotest.tmpdir() as td:
            manifest_path, keyfile = self._setup_artefacts(td)
            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-sign-manifest",
                    str(keyfile), str(manifest_path),
                ]),
                patch("pilo.storage.cloud.subprocess.run"),
            ):
                with pilotest.suppress_stdout():
                    mod.main()

    def test_missing_args_exits(self):
        mod = pilotest.import_command("storage-cloud-sign-manifest")
        with (
            patch("sys.argv", ["pilo-storage-cloud-sign-manifest"]),
            patch("sys.stderr"),
        ):
            with self.assertRaises(SystemExit) as cm:
                mod.main()
        self.assertEqual(cm.exception.code, 1)


class TestStorageCloudVerifyCommand(pilotest.TestCase):

    def _setup_artefacts(self, td, stamp="20260528_120000"):
        archive_path = td / f"{stamp}.tar.zst.age"
        content = b"encrypted data"
        archive_path.write_bytes(content)
        entry = cloud.PackageEntry(
            path="20260528/foo.zfs.manifest",
            checksum="abc" * 20, size=100,
        )
        pkg = cloud.PackageManifest(
            archive=f"{stamp}.tar.zst",
            format="tar.zst",
            checksum="def" * 20, size=200,
            created="now", entries=(entry,),
        )
        enc = cloud.EncryptedArchive(
            recipient="age1key",
            name=f"{stamp}.tar.zst.age",
            checksum=fs.hash_file1(archive_path),
            size=archive_path.stat().st_size,
        )
        cm = cloud.CloudManifest(
            version=1, package=pkg, created="now",
            encrypted_archive=enc,
        )
        manifest_path = td / f"{stamp}.tar.zst.age.manifest"
        cloud.write_cloud_manifest(cm, manifest_path)
        sig_path = td / f"{stamp}.tar.zst.age.manifest.minisig"
        sig_path.write_text("valid sig")
        return manifest_path

    def test_valid_invocation(self):
        mod = pilotest.import_command("storage-cloud-verify-manifest")
        with pilotest.tmpdir() as td:
            manifest_path = self._setup_artefacts(td)
            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-verify-manifest",
                    "RWRpubkey", str(manifest_path),
                ]),
                patch("pilo.storage.cloud.subprocess.run"),
            ):
                with pilotest.suppress_stdout():
                    mod.main()

    def test_missing_args_exits(self):
        mod = pilotest.import_command("storage-cloud-verify-manifest")
        with (
            patch("sys.argv", ["pilo-storage-cloud-verify-manifest"]),
            patch("sys.stderr"),
        ):
            with self.assertRaises(SystemExit) as cm:
                mod.main()
        self.assertEqual(cm.exception.code, 1)


class TestVerifyExtractedManifests(pilotest.TestCase):

    def _make_extracted_root(self, td, date="20260528",
                             tamper_file=None):
        root = td / "extracted"
        d = root / date
        d.mkdir(parents=True)
        stream_path = d / "foo.zfs"
        stream_path.write_bytes(b"stream data")
        mf_data = {
            "stream": "foo.zfs",
            "snapshot": "snap",
            "source": "tank/test",
            "guid": "guid",
            "checksum": fs.hash_file1(stream_path),
            "size": stream_path.stat().st_size,
            "created": "now",
        }
        mf_path = d / "foo.zfs.manifest"
        mf_path.write_text(json.dumps(mf_data))
        if tamper_file == "manifest":
            mf_path.write_text('{"corrupted": true}')
        elif tamper_file == "stream":
            stream_path.write_bytes(b"tampered")
        return root

    def test_valid_extraction(self):
        with pilotest.tmpdir() as td:
            extracted = self._make_extracted_root(td)
            mf = extracted / "20260528/foo.zfs.manifest"
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
                entries=(
                    cloud.PackageEntry(
                        path="20260528/foo.zfs.manifest",
                        checksum=fs.hash_file1(mf),
                        size=mf.stat().st_size,
                    ),
                ),
            )
            cloud.verify_extracted_manifests(extracted, manifest)

    def test_checksum_mismatch(self):
        with pilotest.tmpdir() as td:
            extracted = self._make_extracted_root(td, tamper_file="manifest")
            mf = extracted / "20260528/foo.zfs.manifest"
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
                entries=(
                    cloud.PackageEntry(
                        path="20260528/foo.zfs.manifest",
                        checksum="wrong",
                        size=mf.stat().st_size,
                    ),
                ),
            )
            with self.assertRaises(ValueError):
                cloud.verify_extracted_manifests(extracted, manifest)

    def test_size_mismatch(self):
        with pilotest.tmpdir() as td:
            extracted = self._make_extracted_root(td)
            mf = extracted / "20260528/foo.zfs.manifest"
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
                entries=(
                    cloud.PackageEntry(
                        path="20260528/foo.zfs.manifest",
                        checksum=fs.hash_file1(mf),
                        size=mf.stat().st_size + 1,
                    ),
                ),
            )
            with self.assertRaises(ValueError):
                cloud.verify_extracted_manifests(extracted, manifest)

    def test_missing_file(self):
        with pilotest.tmpdir() as td:
            extracted = td / "extracted"
            (extracted / "20260528").mkdir(parents=True)
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
                entries=(
                    cloud.PackageEntry(
                        path="20260528/foo.zfs.manifest",
                        checksum="c", size=1,
                    ),
                ),
            )
            with self.assertRaises(ValueError):
                cloud.verify_extracted_manifests(extracted, manifest)

    def test_not_a_directory(self):
        with pilotest.tmpdir() as td:
            f = td / "not_a_dir"
            f.write_text("not a dir")
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
            )
            with self.assertRaises(ValueError):
                cloud.verify_extracted_manifests(f, manifest)

    def test_multi_date_extraction(self):
        with pilotest.tmpdir() as td:
            extracted = td / "extracted"
            d1 = extracted / "20260528"
            d1.mkdir(parents=True)
            s1 = d1 / "a.zfs"
            s1.write_bytes(b"data a")
            mf1 = d1 / "a.zfs.manifest"
            mf1.write_text(json.dumps({
                "stream": "a.zfs", "snapshot": "s", "source": "t",
                "guid": "g", "checksum": fs.hash_file1(s1),
                "size": s1.stat().st_size, "created": "now",
            }))
            d2 = extracted / "20260529"
            d2.mkdir(parents=True)
            s2 = d2 / "b.zfs"
            s2.write_bytes(b"data b")
            mf2 = d2 / "b.zfs.manifest"
            mf2.write_text(json.dumps({
                "stream": "b.zfs", "snapshot": "s", "source": "t",
                "guid": "g", "checksum": fs.hash_file1(s2),
                "size": s2.stat().st_size, "created": "now",
            }))
            manifest = cloud.PackageManifest(
                archive="m.tar.zst", created="now",
                entries=(
                    cloud.PackageEntry(
                        path="20260528/a.zfs.manifest",
                        checksum=fs.hash_file1(mf1),
                        size=mf1.stat().st_size,
                    ),
                    cloud.PackageEntry(
                        path="20260529/b.zfs.manifest",
                        checksum=fs.hash_file1(mf2),
                        size=mf2.stat().st_size,
                    ),
                ),
            )
            cloud.verify_extracted_manifests(extracted, manifest)


class TestUnpackArchive(pilotest.TestCase):

    def _make_artefacts(self, td, stamp="20260528_120000",
                        date="20260528", tamper_archive=False):
        archive_path = td / f"{stamp}.tar.zst"
        archive_path.write_bytes(b"archive content")
        orig_dir = td / "_orig"
        orig_dir.mkdir()
        stream_path = orig_dir / "foo.zfs"
        stream_path.write_bytes(b"stream data")
        mf_data = {
            "stream": "foo.zfs",
            "snapshot": "snap",
            "source": "tank/test",
            "guid": "guid",
            "checksum": fs.hash_file1(stream_path),
            "size": stream_path.stat().st_size,
            "created": "now",
        }
        mf_path = orig_dir / "foo.zfs.manifest"
        mf_path.write_text(json.dumps(mf_data))
        entry = cloud.PackageEntry(
            path=f"{date}/foo.zfs.manifest",
            checksum=fs.hash_file1(mf_path),
            size=mf_path.stat().st_size,
        )
        pkg = cloud.PackageManifest(
            archive=f"{stamp}.tar.zst",
            format="tar.zst",
            checksum=fs.hash_file1(archive_path),
            size=archive_path.stat().st_size,
            created="now", entries=(entry,),
        )
        cm = cloud.CloudManifest(
            version=1, package=pkg, created="now",
        )
        manifest_path = td / f"{stamp}.tar.zst.age.manifest"
        cloud.write_cloud_manifest(cm, manifest_path)
        if tamper_archive:
            archive_path.write_bytes(b"tampered")
        return manifest_path, archive_path

    @staticmethod
    def _write_stream_artefacts(tmp, date="20260528",
                                stream_content=None):
        d = tmp / date
        d.mkdir()
        sc = b"stream data" if stream_content is None else stream_content
        s = d / "foo.zfs"
        s.write_bytes(sc)
        mf = d / "foo.zfs.manifest"
        mf.write_text(json.dumps({
            "stream": "foo.zfs",
            "snapshot": "snap",
            "source": "tank/test",
            "guid": "guid",
            "checksum": fs.hash_file1(s),
            "size": s.stat().st_size,
            "created": "now",
        }))

    def _mock_tar_extract(self, date="20260528",
                          stream_content=None):
        def mock_extract(args, **kw):
            idx = args.index("-C")
            tmp = Path(args[idx + 1])
            TestUnpackArchive._write_stream_artefacts(
                tmp, date, stream_content,
            )
        return mock_extract

    def test_unpacks_successfully(self):
        with pilotest.tmpdir() as td:
            manifest_path, archive_path = self._make_artefacts(td)
            dst_root = td / "out"
            with patch(
                "pilo.storage.cloud.subprocess.run",
                side_effect=self._mock_tar_extract(),
            ):
                result = cloud.unpack_archive(
                    archive_path, dst_root, manifest_path,
                )

            expected = dst_root / "20260528_120000"
            self.assertEqual(result, expected)
            self.assertTrue(expected.is_dir())
            self.assertTrue(
                (expected / "20260528/foo.zfs.manifest").exists()
            )

    def test_creates_dst_root(self):
        with pilotest.tmpdir() as td:
            manifest_path, archive_path = self._make_artefacts(td)
            dst_root = td / "deep/nested/out"
            with patch(
                "pilo.storage.cloud.subprocess.run",
                side_effect=self._mock_tar_extract(),
            ):
                result = cloud.unpack_archive(
                    archive_path, dst_root, manifest_path,
                )
            self.assertTrue(result.is_dir())

    def test_archive_checksum_mismatch_raises(self):
        with pilotest.tmpdir() as td:
            manifest_path, archive_path = self._make_artefacts(
                td, tamper_archive=True,
            )
            dst_root = td / "out"
            with patch(
                "pilo.storage.cloud.subprocess.run",
                side_effect=self._mock_tar_extract(),
            ):
                with self.assertRaises(ValueError):
                    cloud.unpack_archive(
                        archive_path, dst_root, manifest_path,
                    )

    def test_destination_already_exists_raises(self):
        with pilotest.tmpdir() as td:
            manifest_path, archive_path = self._make_artefacts(td)
            dst_root = td / "out"
            dst_root.mkdir()
            (dst_root / "20260528_120000").mkdir()
            with patch(
                "pilo.storage.cloud.subprocess.run",
                side_effect=self._mock_tar_extract(),
            ):
                with self.assertRaises(ValueError):
                    cloud.unpack_archive(
                        archive_path, dst_root, manifest_path,
                    )

    def test_missing_archive_raises(self):
        with pilotest.tmpdir() as td:
            archive_path = td / "nonexistent.tar.zst"
            pkg = cloud.PackageManifest(
                archive="nonexistent.tar.zst", created="now",
            )
            cm = cloud.CloudManifest(
                version=1, package=pkg, created="now",
            )
            manifest_path = td / "test.age.manifest"
            cloud.write_cloud_manifest(cm, manifest_path)
            dst_root = td / "out"
            with self.assertRaises(ValueError):
                cloud.unpack_archive(
                    archive_path, dst_root, manifest_path,
                )

    def test_missing_manifest_raises(self):
        with pilotest.tmpdir() as td:
            archive_path = td / "test.tar.zst"
            archive_path.write_text("data")
            manifest_path = td / "nonexistent.age.manifest"
            dst_root = td / "out"
            with self.assertRaises(ValueError):
                cloud.unpack_archive(
                    archive_path, dst_root, manifest_path,
                )

    def test_extracted_entry_mismatch_raises(self):
        with pilotest.tmpdir() as td:
            manifest_path, archive_path = self._make_artefacts(td)
            dst_root = td / "out"

            def mock_wrong_stream(args, **kw):
                idx = args.index("-C")
                tmp = Path(args[idx + 1])
                TestUnpackArchive._write_stream_artefacts(
                    tmp, stream_content=b"different content",
                )

            with patch(
                "pilo.storage.cloud.subprocess.run",
                side_effect=mock_wrong_stream,
            ):
                with self.assertRaises(ValueError):
                    cloud.unpack_archive(
                        archive_path, dst_root, manifest_path,
                    )

    def test_extracted_stream_verify_fails_raises(self):
        with pilotest.tmpdir() as td:
            manifest_path, archive_path = self._make_artefacts(td)
            dst_root = td / "out"

            def mock_bad_checksum(args, **kw):
                idx = args.index("-C")
                tmp = Path(args[idx + 1])
                d = tmp / "20260528"
                d.mkdir()
                (d / "foo.zfs").write_bytes(b"stream data")
                (d / "foo.zfs.manifest").write_text(json.dumps({
                    "stream": "foo.zfs",
                    "snapshot": "snap",
                    "source": "tank/test",
                    "guid": "guid",
                    "checksum": "badchecksum",
                    "size": 0,
                    "created": "now",
                }))

            with patch(
                "pilo.storage.cloud.subprocess.run",
                side_effect=mock_bad_checksum,
            ):
                with self.assertRaises(ValueError):
                    cloud.unpack_archive(
                        archive_path, dst_root, manifest_path,
                    )


class TestStorageCloudUnpackCommand(pilotest.TestCase):

    @staticmethod
    def _write_extracted(tmp, date="20260528"):
        d = tmp / date
        d.mkdir()
        s = d / "foo.zfs"
        s.write_bytes(b"stream data")
        mf = d / "foo.zfs.manifest"
        mf.write_text(json.dumps({
            "stream": "foo.zfs",
            "snapshot": "snap",
            "source": "tank/test",
            "guid": "guid",
            "checksum": fs.hash_file1(s),
            "size": s.stat().st_size,
            "created": "now",
        }))

    def _setup_artefacts(self, td, stamp="20260528_120000"):
        archive_path = td / f"{stamp}.tar.zst"
        archive_path.write_bytes(b"archive content")
        orig_dir = td / "_orig"
        orig_dir.mkdir()
        s = orig_dir / "foo.zfs"
        s.write_bytes(b"stream data")
        mf_path = orig_dir / "foo.zfs.manifest"
        mf_path.write_text(json.dumps({
            "stream": "foo.zfs",
            "snapshot": "snap",
            "source": "tank/test",
            "guid": "guid",
            "checksum": fs.hash_file1(s),
            "size": s.stat().st_size,
            "created": "now",
        }))
        entry = cloud.PackageEntry(
            path=f"{stamp[:8]}/foo.zfs.manifest",
            checksum=fs.hash_file1(mf_path),
            size=mf_path.stat().st_size,
        )
        pkg = cloud.PackageManifest(
            archive=f"{stamp}.tar.zst",
            format="tar.zst",
            checksum=fs.hash_file1(archive_path),
            size=archive_path.stat().st_size,
            created="now", entries=(entry,),
        )
        cm = cloud.CloudManifest(
            version=1, package=pkg, created="now",
        )
        manifest_path = td / f"{stamp}.tar.zst.age.manifest"
        cloud.write_cloud_manifest(cm, manifest_path)
        return archive_path, manifest_path

    def _mock_tar_extract(self):
        def mock_extract(args, **kw):
            idx = args.index("-C")
            tmp = Path(args[idx + 1])
            TestStorageCloudUnpackCommand._write_extracted(tmp)
        return mock_extract

    def test_valid_invocation(self):
        mod = pilotest.import_command("storage-cloud-unpack")
        with pilotest.tmpdir() as td:
            archive_path, manifest_path = self._setup_artefacts(td)
            dst_root = td / "out"
            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-unpack",
                    str(archive_path), str(dst_root),
                    str(manifest_path),
                ]),
                patch(
                    "pilo.storage.cloud.subprocess.run",
                    side_effect=self._mock_tar_extract(),
                ),
            ):
                with pilotest.suppress_stdout():
                    mod.main()

            self.assertTrue(
                (dst_root / "20260528_120000").is_dir()
            )

    def test_missing_args_exits(self):
        mod = pilotest.import_command("storage-cloud-unpack")
        with (
            patch("sys.argv", ["pilo-storage-cloud-unpack"]),
            patch("sys.stderr"),
        ):
            with self.assertRaises(SystemExit) as cm:
                mod.main()
        self.assertEqual(cm.exception.code, 1)


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


class TestFullPrimitiveChain(pilotest.TestCase):

    def test_full_chain(self):
        """pack → encrypt → sign → verify → decrypt → unpack"""
        from pilo.storage import cloud
        import json

        def _tar_make(args, **kw):
            out_idx = args.index("-cf")
            Path(args[out_idx + 1]).write_bytes(b"archive content")

        def _tar_extract(args, **kw):
            c_idx = args.index("-C")
            tmp = Path(args[c_idx + 1])
            d = tmp / "20260528"
            d.mkdir()
            (d / "foo.zfs").write_bytes(b"stream data")
            mf = {
                "stream": "foo.zfs",
                "snapshot": "snap",
                "source": "tank/test",
                "guid": "guid",
                "checksum": fs.hash_file1(d / "foo.zfs"),
                "size": (d / "foo.zfs").stat().st_size,
                "created": "now",
            }
            (d / "foo.zfs.manifest").write_text(json.dumps(mf))

        def _age_ops(args, **kw):
            out_idx = args.index("-o")
            out = Path(args[out_idx + 1])
            inp = Path(args[-1])
            if "-d" in args:
                data = inp.read_bytes()
                if data.endswith(b"-age"):
                    data = data[:-4]
                out.write_bytes(data)
            else:
                out.write_bytes(inp.read_bytes() + b"-age")

        def _minisign_sign(args, **kw):
            m_idx = args.index("-Sm")
            manifest = Path(args[m_idx + 1])
            sig = manifest.parent / (manifest.name + ".minisig")
            sig.write_text("sig")

        def _minisign_verify(args, **kw):
            pass

        with pilotest.tmpdir() as td:
            date = "20260528"
            stream_root = td / "streams"
            (stream_root / date).mkdir(parents=True)
            s = stream_root / date / "foo.zfs"
            s.write_bytes(b"stream data")
            mf_path = stream_root / date / "foo.zfs.manifest"
            mf_path.write_text(json.dumps({
                "stream": "foo.zfs",
                "snapshot": "snap",
                "source": "tank/test",
                "guid": "guid",
                "checksum": fs.hash_file1(s),
                "size": s.stat().st_size,
                "created": "now",
            }))

            cloud_root = td / "artefacts"

            with patch("pilo.storage.cloud.subprocess.run",
                        side_effect=_tar_make):
                archive_path = cloud.pack_stream_set(stream_root, cloud_root)
            self.assertTrue(archive_path.exists())
            stamp = archive_path.name.removesuffix(".tar.zst")
            pack_manifest_path = cloud_root / f"{stamp}.tar.zst.manifest"
            self.assertTrue(pack_manifest_path.exists())

            stamp = archive_path.name.removesuffix(".tar.zst")
            keyfile = td / "minisign.key"
            keyfile.write_text("key")
            dec_dir = td / "decrypted"
            dec_dir.mkdir()
            unpack_root = td / "unpacked"

            with patch("pilo.storage.cloud.subprocess.run",
                        side_effect=_age_ops):
                encrypted_path, cm = cloud.encrypt_archive(
                    archive_path, cloud_root, "age1recipient",
                    identity=str(keyfile),
                )
            self.assertTrue(encrypted_path.exists())

            manifest_age_path = cloud_root / f"{stamp}.tar.zst.age.manifest"
            cloud.write_cloud_manifest(cm, manifest_age_path)
            self.assertTrue(manifest_age_path.exists())

            with patch("pilo.storage.cloud.subprocess.run",
                        side_effect=_minisign_sign):
                sig_path = cloud.sign_cloud_manifest(manifest_age_path, keyfile)
            self.assertTrue(sig_path.exists())

            with patch("pilo.storage.cloud.subprocess.run",
                        side_effect=_minisign_verify):
                verified_path = cloud.verify_cloud_manifest(
                    manifest_age_path, "RWTpubkey"
                )
            self.assertEqual(verified_path, encrypted_path)

            with patch("pilo.storage.cloud.subprocess.run",
                        side_effect=_age_ops):
                dec_path = cloud.decrypt_archive(
                    encrypted_path, dec_dir, keyfile,
                )
            self.assertTrue(dec_path.exists())
            self.assertEqual(dec_path.read_bytes(), b"archive content")

            with patch("pilo.storage.cloud.subprocess.run",
                        side_effect=_tar_extract):
                out_dir = cloud.unpack_archive(
                    dec_path, unpack_root, manifest_age_path,
                )
            self.assertTrue(out_dir.is_dir())
            self.assertTrue((out_dir / date / "foo.zfs").exists())
            self.assertEqual(
                (out_dir / date / "foo.zfs").read_bytes(), b"stream data",
            )
            mf_out = out_dir / date / "foo.zfs.manifest"
            self.assertTrue(mf_out.exists())
            loaded = json.loads(mf_out.read_text())
            self.assertEqual(loaded["stream"], "foo.zfs")


class TestIdempotence(pilotest.TestCase):

    def test_verify_cloud_manifest_does_not_mutate(self):
        from pilo.storage import cloud

        with pilotest.tmpdir() as td:
            archive = td / "data.tar.zst.age"
            archive.write_bytes(b"content")
            pkg = cloud.PackageManifest(
                archive="data.tar.zst", checksum="x" * 64,
                size=7, created="now",
            )
            enc = cloud.EncryptedArchive(
                recipient="key", name="data.tar.zst.age",
                checksum=fs.hash_file1(archive),
                size=archive.stat().st_size,
            )
            cm = cloud.CloudManifest(
                version=1, package=pkg, created="now",
                encrypted_archive=enc,
            )
            mp = td / "data.tar.zst.age.manifest"
            cloud.write_cloud_manifest(cm, mp)
            sig = td / "data.tar.zst.age.manifest.minisig"
            sig.write_text("sig")

            mtime_before = mp.stat().st_mtime
            sig_mtime_before = sig.stat().st_mtime

            with patch("pilo.storage.cloud.subprocess.run"):
                cloud.verify_cloud_manifest(mp, "pubkey")

            self.assertEqual(mp.stat().st_mtime, mtime_before)
            self.assertEqual(sig.stat().st_mtime, sig_mtime_before)

    def test_verify_decrypted_archive_does_not_mutate(self):
        from pilo.storage import cloud

        with pilotest.tmpdir() as td:
            content = b"test data"
            fp = td / "data.tar.zst"
            fp.write_bytes(content)
            man = cloud.PackageManifest(
                archive="data.tar.zst",
                checksum=fs.hash_file1(fp),
                size=len(content), created="now",
            )
            mtime_before = fp.stat().st_mtime

            cloud.verify_decrypted_archive(fp, man)

            self.assertEqual(fp.stat().st_mtime, mtime_before)

    def test_atomic_write_json_cleans_up_tmp(self):
        from pilo.storage.cloud import _atomic_write_json

        with pilotest.tmpdir() as td:
            path = td / "test.json"
            _atomic_write_json({"a": 1}, path)

            self.assertTrue(path.exists())
            self.assertFalse(path.with_suffix(path.suffix + ".tmp").exists())

    def test_atomic_write_json_content(self):
        from pilo.storage.cloud import _atomic_write_json

        with pilotest.tmpdir() as td:
            path = td / "test.json"
            _atomic_write_json({"key": "value"}, path)

            data = json.loads(path.read_text())
            self.assertEqual(data, {"key": "value"})


class TestBuildExportStagingTree(pilotest.TestCase):

    def test_copies_manifest_and_stream(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            (sr / "20260528").mkdir(parents=True)
            (sr / "20260528/foo.zfs").write_bytes(b"stream data")
            (sr / "20260528/foo.zfs.manifest").write_text("{}")
            staging = td / "staging"
            rel = Path("20260528/foo.zfs.manifest")
            cloud.build_export_staging_tree(sr, [rel], staging)
            self.assertTrue((staging / rel).exists())
            self.assertTrue(
                (staging / rel.with_suffix("")).exists()
            )

    def test_preserves_structure(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            (sr / "20260528").mkdir(parents=True)
            (sr / "20260529").mkdir(parents=True)
            (sr / "20260528/a.zfs").write_bytes(b"a")
            (sr / "20260528/a.zfs.manifest").write_text("{}")
            (sr / "20260529/b.zfs").write_bytes(b"b")
            (sr / "20260529/b.zfs.manifest").write_text("{}")
            staging = td / "staging"
            cloud.build_export_staging_tree(sr, [
                Path("20260528/a.zfs.manifest"),
                Path("20260529/b.zfs.manifest"),
            ], staging)
            self.assertTrue((staging / "20260528/a.zfs").exists())
            self.assertTrue((staging / "20260529/b.zfs.manifest").exists())

    def test_creates_parent_dirs(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            (sr / "20260528").mkdir(parents=True)
            (sr / "20260528/f.zfs").write_bytes(b"data")
            (sr / "20260528/f.zfs.manifest").write_text("{}")
            staging = td / "deep/nested/staging"
            cloud.build_export_staging_tree(sr, [
                Path("20260528/f.zfs.manifest"),
            ], staging)
            self.assertTrue(staging.is_dir())
            self.assertTrue(
                (staging / "20260528/f.zfs.manifest").exists()
            )

    def test_selected_only(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            (sr / "20260528").mkdir(parents=True)
            (sr / "20260528/a.zfs").write_bytes(b"a")
            (sr / "20260528/a.zfs.manifest").write_text("{}")
            (sr / "20260528/b.zfs").write_bytes(b"b")
            (sr / "20260528/b.zfs.manifest").write_text("{}")
            staging = td / "staging"
            cloud.build_export_staging_tree(sr, [
                Path("20260528/a.zfs.manifest"),
            ], staging)
            self.assertTrue(
                (staging / "20260528/a.zfs.manifest").exists()
            )
            self.assertFalse(
                (staging / "20260528/b.zfs.manifest").exists()
            )


class TestPackStreamSet(pilotest.TestCase):

    def _setup_stream(self, td, date="20260528", name="foo", content=b"data"):
        d = td / date
        d.mkdir(parents=True)
        z = d / f"{name}.zfs"
        z.write_bytes(content)
        m = d / f"{name}.zfs.manifest"
        m.write_text(json.dumps({
            "stream": f"{name}.zfs",
            "snapshot": "s", "source": "t",
            "guid": "g", "checksum": fs.hash_file1(z),
            "size": z.stat().st_size, "created": "now",
        }))
        return m

    def _mock_tar(self, args, **kw):
        idx = args.index("-cf")
        Path(args[idx + 1]).write_bytes(b"archive content")

    def test_successful_pack(self):
        fixed_dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            self._setup_stream(sr)
            cr = td / "cloud"
            cr.mkdir()
            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "p")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                result = cloud.pack_stream_set(sr, cr)
            expected = cr / "20260528_120000.tar.zst"
            self.assertEqual(result, expected)
            self.assertTrue(expected.exists())
            self.assertTrue(
                (cr / "20260528_120000.tar.zst.manifest").exists()
            )

    def test_multi_date_pack(self):
        fixed_dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            self._setup_stream(sr, "20260528", "a")
            self._setup_stream(sr, "20260529", "b")
            cr = td / "cloud"
            cr.mkdir()
            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "p")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                cloud.pack_stream_set(sr, cr)
            pkg = cloud.load_package_manifest(
                cr / "20260528_120000.tar.zst.manifest"
            )
            self.assertEqual(len(pkg.entries), 2)
            paths = {e.path for e in pkg.entries}
            self.assertEqual(
                paths,
                {"20260528/a.zfs.manifest", "20260529/b.zfs.manifest"},
            )

    def test_no_unexported_streams(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            cr = td / "cloud"
            sr.mkdir()
            cr.mkdir()
            with self.assertRaises(ValueError):
                cloud.pack_stream_set(sr, cr)

    def test_creates_cloud_root(self):
        fixed_dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            self._setup_stream(sr)
            cr = td / "cloud"  # does not exist yet
            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "p")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                cloud.pack_stream_set(sr, cr)
            self.assertTrue(cr.is_dir())
            self.assertTrue((cr / "20260528_120000.tar.zst").exists())

    def test_entries_are_stream_root_relative(self):
        fixed_dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            self._setup_stream(sr, "20260528", "a")
            cr = td / "cloud"
            cr.mkdir()
            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "p")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                cloud.pack_stream_set(sr, cr)
            pkg = cloud.load_package_manifest(
                cr / "20260528_120000.tar.zst.manifest"
            )
            self.assertEqual(
                pkg.entries[0].path, "20260528/a.zfs.manifest",
            )

    def test_stamp_is_creation_time_not_date_dir(self):
        fixed_dt = datetime(2026, 6, 1, 3, 0, 0, tzinfo=timezone.utc)
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            self._setup_stream(sr, "20260528", "a")
            cr = td / "cloud"
            cr.mkdir()
            with (
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=self._mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "p")),
                patch("pilo.storage.cloud.datetime") as mock_dt,
            ):
                mock_dt.now.return_value = fixed_dt
                cloud.pack_stream_set(sr, cr)
            self.assertTrue(
                (cr / "20260601_030000.tar.zst").exists()
            )


class TestPackStreamSetCommand(pilotest.TestCase):

    def _setup_stream(self, td, date="20260528", name="foo"):
        d = td / date
        d.mkdir(parents=True)
        z = d / f"{name}.zfs"
        z.write_bytes(b"data")
        m = d / f"{name}.zfs.manifest"
        m.write_text(json.dumps({
            "stream": f"{name}.zfs",
            "snapshot": "s", "source": "t",
            "guid": "g", "checksum": fs.hash_file1(z),
            "size": z.stat().st_size, "created": "now",
        }))

    def test_new_signature(self):
        mod = pilotest.import_command("storage-cloud-pack")
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            self._setup_stream(sr)
            cr = td / "cloud"
            cr.mkdir()

            def _mock_tar(args, **kw):
                idx = args.index("-cf")
                Path(args[idx + 1]).write_bytes(b"archive content")

            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-pack", str(sr), str(cr),
                ]),
                patch("pilo.storage.cloud.subprocess.run",
                      side_effect=_mock_tar),
                patch("pilo.storage.cloud.streams.verify_one",
                      return_value=("OK", "p")),
            ):
                with pilotest.suppress_stdout():
                    mod.main()
            self.assertTrue(len(list(cr.glob("*.tar.zst"))) > 0)

    def test_error_wrapped(self):
        mod = pilotest.import_command("storage-cloud-pack")
        with pilotest.tmpdir() as td:
            sr = td / "nonexistent"
            cr = td / "cloud"
            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-pack", str(sr), str(cr),
                ]),
                patch("sys.stderr"),
            ):
                with pilotest.assert_fatal(self):
                    mod.main()

    def test_missing_args_exits(self):
        mod = pilotest.import_command("storage-cloud-pack")
        with (
            patch("sys.argv", ["pilo-storage-cloud-pack"]),
            patch("sys.stderr"),
        ):
            with self.assertRaises(SystemExit) as cm:
                mod.main()
        self.assertEqual(cm.exception.code, 1)

    def test_one_arg_exits(self):
        mod = pilotest.import_command("storage-cloud-pack")
        with pilotest.tmpdir() as td:
            with (
                patch("sys.argv", [
                    "pilo-storage-cloud-pack", "/tmp/foo",
                ]),
                patch("sys.stderr"),
            ):
                with self.assertRaises(SystemExit) as cm:
                    mod.main()
            self.assertEqual(cm.exception.code, 1)


def _make_cloud_manifest(cloud_root, stamp, entries, signed=True):
    pkg_entries = tuple(
        cloud.PackageEntry(path=rp, checksum=chk, size=sz)
        for rp, chk, sz in entries
    )
    pkg = cloud.PackageManifest(
        archive=f"{stamp}.tar.zst",
        checksum="archive-checksum",
        size=1000,
        created="now",
        entries=pkg_entries,
    )
    enc = cloud.EncryptedArchive(
        recipient="age1test",
        name=f"{stamp}.tar.zst.age",
        checksum="enc-checksum",
        size=500,
    )
    cm = cloud.CloudManifest(
        version=1, package=pkg, created="now", encrypted_archive=enc,
    )
    mf_path = cloud_root / f"{stamp}.tar.zst.age.manifest"
    cloud.write_cloud_manifest(cm, mf_path)
    if signed:
        (mf_path.parent / (mf_path.name + ".minisig")).write_text("dummy sig")
    return mf_path


def _make_stream_manifest(stream_root, date, name, content=b"stream data"):
    d = stream_root / date
    d.mkdir(parents=True, exist_ok=True)
    zfs_path = d / f"{name}.zfs"
    zfs_path.write_bytes(content)
    mf_path = d / f"{name}.zfs.manifest"
    mf_path.write_text(json.dumps({
        "stream": f"{date}/{name}.zfs",
        "snapshot": "snap",
        "source": "tank/test",
        "guid": "guid",
        "checksum": fs.hash_file1(zfs_path),
        "size": zfs_path.stat().st_size,
        "created": "now",
    }))
    return mf_path


class TestIterCloudManifests(pilotest.TestCase):

    def test_empty_cloud_root(self):
        with pilotest.tmpdir() as td:
            results = list(cloud.iter_cloud_manifests(td / "nonexistent"))
        self.assertEqual(results, [])

    def test_no_manifests(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            results = list(cloud.iter_cloud_manifests(cr))
        self.assertEqual(results, [])

    def test_signed_manifest(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("foo.zfs.manifest", "abc", 10)])
            results = list(cloud.iter_cloud_manifests(cr))
        self.assertEqual(len(results), 1)
        path, cm = results[0]
        self.assertEqual(path.name, "20260528_120000.tar.zst.age.manifest")
        self.assertIsInstance(cm, cloud.CloudManifest)

    def test_unsigned_manifest_skipped(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("foo.zfs.manifest", "abc", 10)],
                                 signed=False)
            results = list(cloud.iter_cloud_manifests(cr))
        self.assertEqual(results, [])

    def test_malformed_manifest_skipped(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            bad = cr / "bad.tar.zst.age.manifest"
            bad.write_text("not valid json")
            (cr / "bad.tar.zst.age.manifest.minisig").write_text("sig")
            results = list(cloud.iter_cloud_manifests(cr))
        self.assertEqual(results, [])

    def test_package_manifest_skipped(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            pkg = cloud.PackageManifest(
                archive="pkg.tar.zst", checksum="c", size=1, created="now",
            )
            pkg_path = cr / "pkg.tar.zst.manifest"
            cloud.write_package_manifest(pkg, pkg_path)
            (cr / "pkg.tar.zst.manifest.minisig").write_text("sig")
            results = list(cloud.iter_cloud_manifests(cr))
        self.assertEqual(results, [])

    def test_mixed_signed_and_unsigned(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("a.zfs.manifest", "c1", 1)],
                                 signed=True)
            _make_cloud_manifest(cr, "20260529_120000",
                                 [("b.zfs.manifest", "c2", 2)],
                                 signed=False)
            results = list(cloud.iter_cloud_manifests(cr))
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0][0].name, "20260528_120000.tar.zst.age.manifest",
        )

    def test_multiple_manifests(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("a.zfs.manifest", "c1", 1)])
            _make_cloud_manifest(cr, "20260529_120000",
                                 [("b.zfs.manifest", "c2", 2)])
            results = list(cloud.iter_cloud_manifests(cr))
        self.assertEqual(len(results), 2)


class TestFindExportedStreamManifests(pilotest.TestCase):

    def test_nonexistent_cloud_root(self):
        with pilotest.tmpdir() as td:
            result = cloud.find_exported_stream_manifests(td / "nonexistent")
        self.assertEqual(result, frozenset())

    def test_empty_cloud_root(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            result = cloud.find_exported_stream_manifests(cr)
        self.assertEqual(result, frozenset())

    def test_single_package_single_entry(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("foo.zfs.manifest", "abc", 10)])
            result = cloud.find_exported_stream_manifests(cr)
        self.assertEqual(result, frozenset({"20260528/foo.zfs.manifest"}))

    def test_single_package_multiple_entries(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000", [
                ("a.zfs.manifest", "c1", 1),
                ("b.zfs.manifest", "c2", 2),
            ])
            result = cloud.find_exported_stream_manifests(cr)
        expected = frozenset({
            "20260528/a.zfs.manifest",
            "20260528/b.zfs.manifest",
        })
        self.assertEqual(result, expected)

    def test_unsigned_ignored(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("a.zfs.manifest", "c1", 1)],
                                 signed=False)
            _make_cloud_manifest(cr, "20260529_120000",
                                 [("b.zfs.manifest", "c2", 2)],
                                 signed=True)
            result = cloud.find_exported_stream_manifests(cr)
        self.assertEqual(result, frozenset({"20260529/b.zfs.manifest"}))

    def test_duplicate_entries_deduplicated(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("a.zfs.manifest", "c1", 1)])
            _make_cloud_manifest(cr, "20260528_123000",
                                 [("a.zfs.manifest", "c1", 1)])
            result = cloud.find_exported_stream_manifests(cr)
        self.assertEqual(result, frozenset({"20260528/a.zfs.manifest"}))

    def test_path_with_slash_not_prepended(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("20260528/a.zfs.manifest", "c1", 1)])
            result = cloud.find_exported_stream_manifests(cr)
        self.assertEqual(result, frozenset({"20260528/a.zfs.manifest"}))

    def test_multiple_packages(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("a.zfs.manifest", "c1", 1)])
            _make_cloud_manifest(cr, "20260529_120000",
                                 [("b.zfs.manifest", "c2", 2)])
            result = cloud.find_exported_stream_manifests(cr)
        expected = frozenset({
            "20260528/a.zfs.manifest",
            "20260529/b.zfs.manifest",
        })
        self.assertEqual(result, expected)

    def test_with_pubkey_calls_is_authoritative(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("a.zfs.manifest", "c1", 1)])
            with patch(
                "pilo.storage.cloud.is_authoritative_cloud_manifest",
                return_value=True,
            ) as mock_auth:
                result = cloud.find_exported_stream_manifests(
                    cr, pubkey="pubkey",
                )
        self.assertEqual(result, frozenset({"20260528/a.zfs.manifest"}))
        mock_auth.assert_called_once()

    def test_with_pubkey_excludes_non_authoritative(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("a.zfs.manifest", "c1", 1)])
            with patch(
                "pilo.storage.cloud.is_authoritative_cloud_manifest",
                return_value=False,
            ):
                result = cloud.find_exported_stream_manifests(
                    cr, pubkey="pubkey",
                )
        self.assertEqual(result, frozenset())

    def test_without_pubkey_uses_old_heuristic(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("a.zfs.manifest", "c1", 1)])
            with patch(
                "pilo.storage.cloud.is_authoritative_cloud_manifest",
            ) as mock_auth:
                result = cloud.find_exported_stream_manifests(cr)
        self.assertEqual(result, frozenset({"20260528/a.zfs.manifest"}))
        mock_auth.assert_not_called()


class TestFindUnexportedStreamManifests(pilotest.TestCase):

    def test_stream_root_missing(self):
        with pilotest.tmpdir() as td:
            with self.assertRaises(ValueError):
                cloud.find_unexported_stream_manifests(
                    td / "nonexistent", td / "cloud",
                )

    def test_all_unexported(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            cr = td / "cloud"
            sr.mkdir()
            cr.mkdir()
            _make_stream_manifest(sr, "20260528", "foo")
            result = cloud.find_unexported_stream_manifests(sr, cr)
        self.assertEqual(result, [Path("20260528/foo.zfs.manifest")])

    def test_some_exported(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            cr = td / "cloud"
            sr.mkdir()
            cr.mkdir()
            _make_stream_manifest(sr, "20260528", "foo")
            _make_stream_manifest(sr, "20260528", "bar")
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("foo.zfs.manifest", "c1", 1)])
            result = cloud.find_unexported_stream_manifests(sr, cr)
        self.assertEqual(result, [Path("20260528/bar.zfs.manifest")])

    def test_all_exported(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            cr = td / "cloud"
            sr.mkdir()
            cr.mkdir()
            _make_stream_manifest(sr, "20260528", "foo")
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("foo.zfs.manifest", "c1", 1)])
            result = cloud.find_unexported_stream_manifests(sr, cr)
        self.assertEqual(result, [])

    def test_multiple_date_dirs(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            cr = td / "cloud"
            sr.mkdir()
            cr.mkdir()
            _make_stream_manifest(sr, "20260528", "a")
            _make_stream_manifest(sr, "20260529", "b")
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("a.zfs.manifest", "c1", 1)])
            result = cloud.find_unexported_stream_manifests(sr, cr)
        self.assertEqual(result, [Path("20260529/b.zfs.manifest")])

    def test_cloud_root_nonexistent(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            sr.mkdir()
            _make_stream_manifest(sr, "20260528", "foo")
            result = cloud.find_unexported_stream_manifests(
                sr, td / "nonexistent",
            )
        self.assertEqual(result, [Path("20260528/foo.zfs.manifest")])

    def test_no_stream_manifests(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            cr = td / "cloud"
            sr.mkdir()
            cr.mkdir()
            (sr / "20260528").mkdir()
            result = cloud.find_unexported_stream_manifests(sr, cr)
        self.assertEqual(result, [])

    def test_returns_sorted(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            cr = td / "cloud"
            sr.mkdir()
            cr.mkdir()
            _make_stream_manifest(sr, "20260528", "z")
            _make_stream_manifest(sr, "20260528", "a")
            result = cloud.find_unexported_stream_manifests(sr, cr)
        self.assertEqual(result, [
            Path("20260528/a.zfs.manifest"),
            Path("20260528/z.zfs.manifest"),
        ])

    def test_duplicate_export_membership(self):
        with pilotest.tmpdir() as td:
            sr = td / "streams"
            cr = td / "cloud"
            sr.mkdir()
            cr.mkdir()
            _make_stream_manifest(sr, "20260528", "a")
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("a.zfs.manifest", "c1", 1)])
            _make_cloud_manifest(cr, "20260528_123000",
                                 [("a.zfs.manifest", "c1", 1)])
            result = cloud.find_unexported_stream_manifests(sr, cr)
        self.assertEqual(result, [])


class TestFindDuplicateExportMembership(pilotest.TestCase):

    def test_nonexistent_cloud_root(self):
        with pilotest.tmpdir() as td:
            result = cloud.find_duplicate_export_membership(
                td / "nonexistent",
            )
        self.assertEqual(result, {})

    def test_empty_cloud_root(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            result = cloud.find_duplicate_export_membership(cr)
        self.assertEqual(result, {})

    def test_no_duplicates(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("foo.zfs.manifest", "abc", 10)])
            result = cloud.find_duplicate_export_membership(cr)
        self.assertEqual(result, {})

    def test_single_duplicate(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("20260528/a.zfs.manifest", "c1", 1)])
            _make_cloud_manifest(cr, "20260529_080000",
                                 [("20260528/a.zfs.manifest", "c1", 1)])
            result = cloud.find_duplicate_export_membership(cr)
        self.assertEqual(
            result,
            {"20260528/a.zfs.manifest": ["20260528_120000", "20260529_080000"]},
        )

    def test_multiple_duplicates(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("20260528/a.zfs.manifest", "c1", 1),
                                  ("20260528/b.zfs.manifest", "c2", 2)])
            _make_cloud_manifest(cr, "20260529_080000",
                                 [("20260528/a.zfs.manifest", "c1", 1),
                                  ("20260528/b.zfs.manifest", "c2", 2)])
            result = cloud.find_duplicate_export_membership(cr)
        self.assertEqual(len(result), 2)

    def test_three_way_duplicate(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("20260528/a.zfs.manifest", "c1", 1)])
            _make_cloud_manifest(cr, "20260529_080000",
                                 [("20260528/a.zfs.manifest", "c1", 1)])
            _make_cloud_manifest(cr, "20260530_080000",
                                 [("20260528/a.zfs.manifest", "c1", 1)])
            result = cloud.find_duplicate_export_membership(cr)
        stamps = result["20260528/a.zfs.manifest"]
        self.assertEqual(len(stamps), 3)

    def test_unsigned_ignored(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("20260528/a.zfs.manifest", "c1", 1)],
                                 signed=True)
            _make_cloud_manifest(cr, "20260529_080000",
                                 [("20260528/a.zfs.manifest", "c1", 1)],
                                 signed=False)
            result = cloud.find_duplicate_export_membership(cr)
        self.assertEqual(result, {})

    def test_different_entries_not_flagged(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("20260528/a.zfs.manifest", "c1", 1)])
            _make_cloud_manifest(cr, "20260529_080000",
                                 [("20260528/b.zfs.manifest", "c2", 2)])
            result = cloud.find_duplicate_export_membership(cr)
        self.assertEqual(result, {})

    def test_with_pubkey_excludes_non_authoritative(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir()
            _make_cloud_manifest(cr, "20260528_120000",
                                 [("20260528/a.zfs.manifest", "c1", 1)])
            _make_cloud_manifest(cr, "20260529_080000",
                                 [("20260528/a.zfs.manifest", "c1", 1)])
            with patch(
                "pilo.storage.cloud.is_authoritative_cloud_manifest",
                side_effect=lambda p, pk: "20260528" in str(p),
            ):
                result = cloud.find_duplicate_export_membership(
                    cr, pubkey="pk",
                )
        self.assertEqual(result, {})


class TestIsAuthoritativeCloudManifest(pilotest.TestCase):

    def _make_age_manifest(self, td, stamp="20260528_120000",
                           with_sig=True, with_enc_meta=True,
                           archive_content=b"encrypted data"):
        cr = td / "cloud"
        cr.mkdir(exist_ok=True)
        enc_name = f"{stamp}.tar.zst.age"
        archive_path = cr / enc_name
        archive_path.write_bytes(archive_content)
        enc_checksum = fs.hash_file1(archive_path)
        enc_size = archive_path.stat().st_size
        enc = cloud.EncryptedArchive(
            recipient="age1test",
            name=enc_name,
            checksum=enc_checksum,
            size=enc_size,
        ) if with_enc_meta else None
        pkg = cloud.PackageManifest(
            archive=f"{stamp}.tar.zst",
            checksum="archive-checksum", size=1000,
            created="now",
        )
        cm = cloud.CloudManifest(
            version=1, package=pkg, created="now",
            encrypted_archive=enc,
        )
        mf_path = cr / f"{stamp}.tar.zst.age.manifest"
        cloud.write_cloud_manifest(cm, mf_path)
        if with_sig:
            (mf_path.parent / (mf_path.name + ".minisig")).write_text("sig")
        return mf_path

    def test_nonexistent_manifest(self):
        with pilotest.tmpdir() as td:
            result = cloud.is_authoritative_cloud_manifest(
                td / "nonexistent", "pubkey",
            )
        self.assertFalse(result)

    def test_missing_minisig(self):
        with pilotest.tmpdir() as td:
            mf = self._make_age_manifest(td, with_sig=False)
            result = cloud.is_authoritative_cloud_manifest(mf, "pubkey")
        self.assertFalse(result)

    def test_invalid_signature(self):
        with pilotest.tmpdir() as td:
            mf = self._make_age_manifest(td, with_sig=True)
            with patch("pilo.storage.cloud.subprocess.run",
                       side_effect=CalledProcessError(
                           1, ["minisign"])):
                result = cloud.is_authoritative_cloud_manifest(mf, "pubkey")
        self.assertFalse(result)

    def test_no_encrypted_archive_metadata(self):
        with pilotest.tmpdir() as td:
            mf = self._make_age_manifest(td, with_enc_meta=False)
            result = cloud.is_authoritative_cloud_manifest(mf, "pubkey")
        self.assertFalse(result)

    def test_missing_encrypted_archive_file(self):
        with pilotest.tmpdir() as td:
            cr = td / "cloud"
            cr.mkdir(exist_ok=True)
            enc = cloud.EncryptedArchive(
                recipient="age1test",
                name="nonexistent.tar.zst.age",
                checksum="csum", size=100,
            )
            pkg = cloud.PackageManifest(
                archive="s.tar.zst", checksum="c", size=1,
                created="now",
            )
            cm = cloud.CloudManifest(
                version=1, package=pkg, created="now",
                encrypted_archive=enc,
            )
            mf_path = cr / "s.tar.zst.age.manifest"
            cloud.write_cloud_manifest(cm, mf_path)
            (mf_path.parent / (mf_path.name + ".minisig")).write_text("sig")
            with patch("pilo.storage.cloud.subprocess.run"):
                result = cloud.is_authoritative_cloud_manifest(mf_path, "pubkey")
        self.assertFalse(result)

    def test_checksum_mismatch(self):
        with pilotest.tmpdir() as td:
            mf = self._make_age_manifest(
                td, archive_content=b"original content",
            )
            cr = td / "cloud"
            archive_path = cr / "20260528_120000.tar.zst.age"
            archive_path.write_bytes(b"tampered content")
            with patch("pilo.storage.cloud.subprocess.run"):
                result = cloud.is_authoritative_cloud_manifest(mf, "pubkey")
        self.assertFalse(result)

    def test_authoritative(self):
        with pilotest.tmpdir() as td:
            mf = self._make_age_manifest(
                td, archive_content=b"valid content",
            )
            with patch("pilo.storage.cloud.subprocess.run"):
                result = cloud.is_authoritative_cloud_manifest(mf, "pubkey")
        self.assertTrue(result)

    def test_cached_result(self):
        with pilotest.tmpdir() as td:
            mf = self._make_age_manifest(
                td, archive_content=b"valid content",
            )
            with patch("pilo.storage.cloud.subprocess.run") as mock_run:
                first = cloud.is_authoritative_cloud_manifest(mf, "pubkey")
                second = cloud.is_authoritative_cloud_manifest(mf, "pubkey")
            self.assertTrue(first)
            self.assertTrue(second)
            self.assertEqual(mock_run.call_count, 1)
