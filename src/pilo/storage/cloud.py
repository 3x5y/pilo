import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from . import streams
from .. import fs


STREAM_SUFFIX = ".zfs"
MANIFEST_SUFFIX = ".zfs.manifest"

_VALID_STAMP_RE = re.compile(r"^\d{8}_\d{6}$")
_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")


@dataclass(frozen=True)
class PackageEntry:
    path: str
    checksum: str
    size: int

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "checksum": self.checksum,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PackageEntry":
        try:
            size = d["size"]
            if not isinstance(size, int):
                raise ValueError("size must be int")
            return cls(
                path=d["path"],
                checksum=d["checksum"],
                size=size,
            )
        except KeyError as e:
            raise ValueError(f"missing field: {e}") from e


@dataclass(frozen=True)
class PackageManifest:
    archive: str
    format: str = "tar.zst"
    checksum: str = ""
    size: int = 0
    created: str = ""
    entries: tuple[PackageEntry, ...] = ()

    def to_dict(self) -> dict:
        return {
            "archive": self.archive,
            "format": self.format,
            "checksum": self.checksum,
            "size": self.size,
            "created": self.created,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PackageManifest":
        try:
            size = d["size"]
            if not isinstance(size, int):
                raise ValueError("size must be int")
            entries_raw = d["entries"]
            if not isinstance(entries_raw, list):
                raise ValueError("entries must be a list")
            entries = tuple(PackageEntry.from_dict(e) for e in entries_raw)
            _validate_package_entries(entries)
            return cls(
                archive=d["archive"],
                format=d.get("format", "tar.zst"),
                checksum=d["checksum"],
                size=size,
                created=d["created"],
                entries=entries,
            )
        except KeyError as e:
            raise ValueError(f"missing field: {e}") from e


@dataclass(frozen=True)
class EncryptedArchive:
    recipient: str
    name: str
    checksum: str
    size: int
    format: str = "age"

    def to_dict(self) -> dict:
        return {
            "format": self.format,
            "recipient": self.recipient,
            "name": self.name,
            "checksum": self.checksum,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EncryptedArchive":
        try:
            size = d["size"]
            if not isinstance(size, int):
                raise ValueError("size must be int")
            return cls(
                recipient=d["recipient"],
                name=d["name"],
                checksum=d["checksum"],
                size=size,
                format=d.get("format", "age"),
            )
        except KeyError as e:
            raise ValueError(f"missing field: {e}") from e


@dataclass(frozen=True)
class CloudManifest:
    version: int
    package: PackageManifest
    created: str
    encrypted_archive: EncryptedArchive | None = None

    def to_dict(self) -> dict:
        d = {
            "version": self.version,
            "package": self.package.to_dict(),
            "created": self.created,
        }
        if self.encrypted_archive is not None:
            d["encrypted_archive"] = self.encrypted_archive.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "CloudManifest":
        try:
            version = d["version"]
            if not isinstance(version, int):
                raise ValueError("version must be int")
            encrypted_archive = None
            if "encrypted_archive" in d:
                encrypted_archive = EncryptedArchive.from_dict(d["encrypted_archive"])
            return cls(
                version=version,
                package=PackageManifest.from_dict(d["package"]),
                created=d["created"],
                encrypted_archive=encrypted_archive,
            )
        except KeyError as e:
            raise ValueError(f"missing field: {e}") from e


def validate_pack_input(src_dir: Path, dst_dir: Path, stamp: str) -> None:
    if not src_dir.is_dir():
        raise ValueError(f"not a directory: {src_dir}")
    if not _VALID_STAMP_RE.match(stamp):
        raise ValueError(f"invalid stamp, expected YYYYMMDD_HHMMSS: {stamp}")
    if dst_dir.exists() and not dst_dir.is_dir():
        raise ValueError(f"output path exists and is not a directory: {dst_dir}")
    archive_path = dst_dir / f"{stamp}.tar.zst"
    if archive_path.exists():
        raise ValueError(f"output already exists: {archive_path}")
    manifest_path = dst_dir / f"{stamp}.tar.zst.manifest"
    if manifest_path.exists():
        raise ValueError(f"output already exists: {manifest_path}")

    for f in sorted(src_dir.iterdir()):
        if f.is_symlink():
            raise ValueError(f"symlink not allowed: {f.name}")
        if f.is_dir():
            raise ValueError(f"nested directory not allowed: {f.name}")
        if not f.is_file():
            raise ValueError(f"unexpected entry type: {f.name}")
        if f.name.startswith("."):
            raise ValueError(f"hidden file not allowed: {f.name}")
        if not _SAFE_FILENAME_RE.match(f.name):
            raise ValueError(f"malformed filename: {f.name}")
        if not (f.name.endswith(STREAM_SUFFIX) or f.name.endswith(MANIFEST_SUFFIX)):
            raise ValueError(f"unexpected file type: {f.name}")


def build_package_manifest(
    stamp: str,
    archive_checksum: str,
    archive_size: int,
    created: str,
    entries: tuple[PackageEntry, ...],
) -> PackageManifest:
    return PackageManifest(
        archive=f"{stamp}.tar.zst",
        format="tar.zst",
        checksum=archive_checksum,
        size=archive_size,
        created=created,
        entries=entries,
    )


def pack_stream_day(src_dir: Path, dst_dir: Path) -> Path:
    now = datetime.now(timezone.utc)
    date_prefix = src_dir.name
    stamp = f"{date_prefix}_{now.strftime('%H%M%S')}"
    validate_pack_input(src_dir, dst_dir, stamp)
    dst_dir.mkdir(parents=True, exist_ok=True)

    manifest_files = sorted(src_dir.glob(f"*{MANIFEST_SUFFIX}"))
    if not manifest_files:
        raise ValueError("no stream manifests found")

    for mf in manifest_files:
        status, msg = streams.verify_one(mf)
        if status != "OK":
            raise ValueError(f"stream verification failed: {msg}")

    created = now.isoformat()

    with TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        tmp_archive = tmp_dir / f"{stamp}.tar.zst"

        subprocess.run(
            [
                "tar", "--zstd", "-cf", str(tmp_archive),
                "-C", str(src_dir.parent),
                "--sort=name",
                "--owner=0:0", "--group=0:0",
                #"--mode=644", # stuffs up directory perms
                "--mtime=@0",
                date_prefix,
            ],
            check=True,
        )

        archive_checksum = fs.hash_file1(tmp_archive)
        archive_size = tmp_archive.stat().st_size

        entries = []
        for mf in manifest_files:
            rel = str(mf.relative_to(src_dir))
            entries.append(PackageEntry(
                path=rel,
                checksum=fs.hash_file1(mf),
                size=mf.stat().st_size,
            ))

        manifest = build_package_manifest(
            stamp=stamp,
            archive_checksum=archive_checksum,
            archive_size=archive_size,
            created=created,
            entries=tuple(entries),
        )
        tmp_manifest = tmp_dir / f"{stamp}.tar.zst.manifest"
        write_package_manifest(manifest, tmp_manifest)

        dst_archive = dst_dir / f"{stamp}.tar.zst"
        dst_manifest = dst_dir / f"{stamp}.tar.zst.manifest"
        shutil.move(str(tmp_archive), str(dst_archive))
        shutil.move(str(tmp_manifest), str(dst_manifest))

    return dst_archive


_AGE_SUFFIX = ".age"


def encrypt_archive(
    archive_path: Path,
    dst_dir: Path,
    recipient: str,
    identity: str | None = None,
) -> tuple[Path, CloudManifest]:
    if not archive_path.is_file():
        raise ValueError(f"not a file: {archive_path}")
    if not recipient:
        raise ValueError("recipient must not be empty")

    name = archive_path.name
    if not name.endswith(".tar.zst"):
        raise ValueError(f"unexpected archive extension: {name}")
    stamp = name.removesuffix(".tar.zst")

    manifest_path = archive_path.parent / f"{stamp}.tar.zst.manifest"
    if not manifest_path.is_file():
        raise ValueError(f"manifest not found: {manifest_path}")

    pkg_manifest = load_package_manifest(manifest_path)
    actual_checksum = fs.hash_file1(archive_path)
    if actual_checksum != pkg_manifest.checksum:
        raise ValueError(f"archive checksum mismatch: {archive_path}")

    encrypted_name = f"{stamp}.tar.zst{_AGE_SUFFIX}"
    encrypted_path = dst_dir / encrypted_name
    if encrypted_path.exists():
        raise ValueError(f"output already exists: {encrypted_path}")
    age_manifest_name = f"{stamp}.tar.zst{_AGE_SUFFIX}.manifest"
    age_manifest_path = dst_dir / age_manifest_name
    if age_manifest_path.exists():
        raise ValueError(f"output already exists: {age_manifest_path}")

    dst_dir.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        tmp_encrypted = tmp_dir / encrypted_name

        subprocess.run(
            ["age", "-r", recipient, "-o", str(tmp_encrypted), str(archive_path)],
            check=True,
        )

        enc_checksum = fs.hash_file1(tmp_encrypted)
        enc_size = tmp_encrypted.stat().st_size

        if identity is not None:
            tmp_decrypted = tmp_dir / f"{stamp}.tar.zst"
            subprocess.run(
                [
                    "age", "-d", "-i", identity,
                    "-o", str(tmp_decrypted), str(tmp_encrypted),
                ],
                check=True,
            )
            dec_checksum = fs.hash_file1(tmp_decrypted)
            if dec_checksum != pkg_manifest.checksum:
                raise ValueError(
                    "decrypted archive checksum mismatch"
                )

        encrypted_archive = EncryptedArchive(
            recipient=recipient,
            name=encrypted_name,
            checksum=enc_checksum,
            size=enc_size,
            format="age",
        )

        cloud_manifest = CloudManifest(
            version=1,
            package=pkg_manifest,
            created=pkg_manifest.created,
            encrypted_archive=encrypted_archive,
        )

        shutil.move(str(tmp_encrypted), str(encrypted_path))

    return encrypted_path, cloud_manifest


def sign_cloud_manifest(manifest_path: Path, keyfile: Path) -> Path:
    if not manifest_path.is_file():
        raise ValueError(f"manifest not found: {manifest_path}")
    if not keyfile:
        raise ValueError("keyfile must not be empty")

    manifest = load_cloud_manifest(manifest_path)
    if manifest.encrypted_archive is None:
        raise ValueError("manifest has no encrypted archive metadata")

    enc = manifest.encrypted_archive
    archive_path = manifest_path.parent / enc.name
    actual = fs.hash_file1(archive_path)
    if actual != enc.checksum:
        raise ValueError(
            f"encrypted archive checksum mismatch: {archive_path}"
        )

    sig_path = manifest_path.parent / (manifest_path.name + ".minisig")
    if sig_path.exists():
        raise ValueError(f"signature already exists: {sig_path}")

    subprocess.run(
        ["minisign", "-Sm", str(manifest_path), "-s", str(keyfile)],
        check=True,
    )

    return sig_path


def verify_cloud_manifest(manifest_path: Path, pubkey: str) -> Path:
    if not manifest_path.is_file():
        raise ValueError(f"manifest not found: {manifest_path}")
    if not pubkey:
        raise ValueError("pubkey must not be empty")

    sig_path = manifest_path.parent / (manifest_path.name + ".minisig")
    if not sig_path.is_file():
        raise ValueError(f"signature not found: {sig_path}")

    try:
        subprocess.run(
            ["minisign", "-Vm", str(manifest_path), "-P", pubkey],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        raise ValueError("signature verification failed")

    manifest = load_cloud_manifest(manifest_path)
    if manifest.encrypted_archive is None:
        raise ValueError("manifest has no encrypted archive metadata")

    enc = manifest.encrypted_archive
    archive_path = manifest_path.parent / enc.name
    actual = fs.hash_file1(archive_path)
    if actual != enc.checksum:
        raise ValueError(
            f"encrypted archive checksum mismatch: {archive_path}"
        )

    return archive_path


def verify_decrypted_archive(
    decrypted_path: Path,
    manifest: PackageManifest,
) -> None:
    actual_checksum = fs.hash_file1(decrypted_path)
    if actual_checksum != manifest.checksum:
        raise ValueError(
            f"decrypted archive checksum mismatch: {decrypted_path}"
        )
    actual_size = decrypted_path.stat().st_size
    if actual_size != manifest.size:
        raise ValueError(
            f"decrypted archive size mismatch: {decrypted_path}"
        )


def decrypt_archive(
    archive_path: Path,
    dst_dir: Path,
    identity: Path,
) -> Path:
    if not archive_path.is_file():
        raise ValueError(f"not a file: {archive_path}")
    if not identity.is_file():
        raise ValueError(f"identity not found: {identity}")

    name = archive_path.name
    if not name.endswith(".tar.zst.age"):
        raise ValueError(f"unexpected archive extension: {name}")
    stamp = name.removesuffix(".tar.zst.age")

    manifest_path = archive_path.parent / f"{name}.manifest"
    if not manifest_path.is_file():
        raise ValueError(f"manifest not found: {manifest_path}")

    cloud_manifest = load_cloud_manifest(manifest_path)
    if cloud_manifest.encrypted_archive is None:
        raise ValueError("manifest has no encrypted archive metadata")

    enc = cloud_manifest.encrypted_archive
    actual = fs.hash_file1(archive_path)
    if actual != enc.checksum:
        raise ValueError(
            f"encrypted archive checksum mismatch: {archive_path}"
        )

    output_name = f"{stamp}.tar.zst"
    output_path = dst_dir / output_name
    if output_path.exists():
        raise ValueError(f"output already exists: {output_path}")

    dst_dir.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        tmp_output = tmp_dir / output_name

        try:
            subprocess.run(
                [
                    "age", "-d", "-i", str(identity),
                    "-o", str(tmp_output), str(archive_path),
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            raise ValueError("decryption failed")

        verify_decrypted_archive(tmp_output, cloud_manifest.package)

        shutil.move(str(tmp_output), str(output_path))

    return output_path


def verify_extracted_manifests(
    extracted_dir: Path,
    manifest: PackageManifest,
) -> None:
    if not extracted_dir.is_dir():
        raise ValueError(f"not a directory: {extracted_dir}")
    if not re.match(r"^\d{8}$", extracted_dir.name):
        raise ValueError(
            f"unexpected directory name: {extracted_dir.name}"
        )

    for entry in manifest.entries:
        file_path = extracted_dir / entry.path
        if not file_path.is_file():
            raise ValueError(f"missing extracted file: {file_path}")
        actual_checksum = fs.hash_file1(file_path)
        if actual_checksum != entry.checksum:
            raise ValueError(f"checksum mismatch: {file_path}")
        actual_size = file_path.stat().st_size
        if actual_size != entry.size:
            raise ValueError(f"size mismatch: {file_path}")

    for mf in sorted(extracted_dir.rglob(f"*{MANIFEST_SUFFIX}")):
        status, msg = streams.verify_one(mf)
        if status != "OK":
            raise ValueError(f"stream verification failed: {msg}")


def unpack_archive(
    archive_path: Path,
    dst_root: Path,
    manifest_path: Path,
) -> Path:
    if not archive_path.is_file():
        raise ValueError(f"not a file: {archive_path}")
    if not manifest_path.is_file():
        raise ValueError(f"manifest not found: {manifest_path}")

    cloud_manifest = load_cloud_manifest(manifest_path)
    pkg = cloud_manifest.package

    actual_checksum = fs.hash_file1(archive_path)
    if actual_checksum != pkg.checksum:
        raise ValueError(
            f"archive checksum mismatch: {archive_path}"
        )

    with TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        subprocess.run(
            [
                "tar", "--zstd", "-xf", str(archive_path),
                "--touch", # use current time for mtime
                "-C", str(tmp_dir),
            ],
            check=True,
        )

        contents = list(tmp_dir.iterdir())
        if len(contents) != 1 or not contents[0].is_dir():
            raise ValueError(
                "archive must contain a single directory"
            )

        extracted_dir = contents[0]
        if not re.match(r"^\d{8}$", extracted_dir.name):
            raise ValueError(
                f"unexpected directory name: {extracted_dir.name}"
            )

        dst_path = dst_root / extracted_dir.name
        if dst_path.exists():
            raise ValueError(
                f"destination already exists: {dst_path}"
            )

        verify_extracted_manifests(extracted_dir, pkg)

        dst_root.mkdir(parents=True, exist_ok=True)
        shutil.move(str(extracted_dir), str(dst_path))

    return dst_path


def _validate_package_entries(entries: tuple[PackageEntry, ...]) -> None:
    for entry in entries:
        p = entry.path
        if os.path.isabs(p):
            raise ValueError(f"absolute path not allowed: {p}")
        if p.endswith(STREAM_SUFFIX) and not p.endswith(MANIFEST_SUFFIX):
            raise ValueError(f".zfs stream path not allowed: {p}")


def write_package_manifest(manifest: PackageManifest, path: Path) -> None:
    text = json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n"
    path.write_text(text)


def load_package_manifest(path: Path) -> PackageManifest:
    data = json.loads(path.read_text())
    return PackageManifest.from_dict(data)


def write_cloud_manifest(manifest: CloudManifest, path: Path) -> None:
    text = json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n"
    path.write_text(text)


def load_cloud_manifest(path: Path) -> CloudManifest:
    data = json.loads(path.read_text())
    return CloudManifest.from_dict(data)
