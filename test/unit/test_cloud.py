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
                result = cloud.pack_stream_day(src, dst)

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

    def _make_extracted_dir(self, td, date="20260528",
                            tamper_file=None):
        d = td / date
        d.mkdir()
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
        return d

    def test_valid_extraction(self):
        with pilotest.tmpdir() as td:
            d = self._make_extracted_dir(td)
            mf = d / "foo.zfs.manifest"
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
                entries=(
                    cloud.PackageEntry(
                        path="foo.zfs.manifest",
                        checksum=fs.hash_file1(mf),
                        size=mf.stat().st_size,
                    ),
                ),
            )
            cloud.verify_extracted_manifests(d, manifest)

    def test_checksum_mismatch(self):
        with pilotest.tmpdir() as td:
            d = self._make_extracted_dir(td, tamper_file="manifest")
            mf = d / "foo.zfs.manifest"
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
                entries=(
                    cloud.PackageEntry(
                        path="foo.zfs.manifest",
                        checksum="wrong",
                        size=mf.stat().st_size,
                    ),
                ),
            )
            with self.assertRaises(ValueError):
                cloud.verify_extracted_manifests(d, manifest)

    def test_size_mismatch(self):
        with pilotest.tmpdir() as td:
            d = self._make_extracted_dir(td)
            mf = d / "foo.zfs.manifest"
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
                entries=(
                    cloud.PackageEntry(
                        path="foo.zfs.manifest",
                        checksum=fs.hash_file1(mf),
                        size=mf.stat().st_size + 1,
                    ),
                ),
            )
            with self.assertRaises(ValueError):
                cloud.verify_extracted_manifests(d, manifest)

    def test_missing_file(self):
        with pilotest.tmpdir() as td:
            d = td / "20260528"
            d.mkdir()
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
                entries=(
                    cloud.PackageEntry(
                        path="foo.zfs.manifest",
                        checksum="c", size=1,
                    ),
                ),
            )
            with self.assertRaises(ValueError):
                cloud.verify_extracted_manifests(d, manifest)

    def test_not_a_directory(self):
        with pilotest.tmpdir() as td:
            f = td / "20260528"
            f.write_text("not a dir")
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
            )
            with self.assertRaises(ValueError):
                cloud.verify_extracted_manifests(f, manifest)

    def test_bad_directory_name(self):
        with pilotest.tmpdir() as td:
            d = td / "not-a-date"
            d.mkdir()
            manifest = cloud.PackageManifest(
                archive="a.tar.zst", created="now",
            )
            with self.assertRaises(ValueError):
                cloud.verify_extracted_manifests(d, manifest)


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
            path="foo.zfs.manifest",
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

            expected = dst_root / "20260528"
            self.assertEqual(result, expected)
            self.assertTrue(expected.is_dir())
            self.assertTrue(
                (expected / "foo.zfs.manifest").exists()
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
            (dst_root / "20260528").mkdir()
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
            path="foo.zfs.manifest",
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
                (dst_root / "20260528").is_dir()
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
