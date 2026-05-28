import unittest

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
