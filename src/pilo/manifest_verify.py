from pathlib import Path

from . import fs

from .manifest_codec import render_manifest_entry
from .manifest_model import ManifestEntry


def generate_manifest_entries(root: Path, exclude=None):
    exclude = set(exclude or [])

    for path in sorted(fs.iter_files(root)):
        rel = path.relative_to(root)

        if rel in exclude:
            continue

        checksum = fs.sha256_file(path)
        yield ManifestEntry(checksum, rel)


def generate_manifest_lines(root: Path, exclude=None):
    for entry in generate_manifest_entries(root, exclude):
        yield render_manifest_entry(entry)


def verify_manifest_lines(root: Path, lines, exclude=None):
    root = Path(root)
    exclude = set(exclude or [])

    expected = {}

    for line in lines:
        line = line.strip()

        if not line:
            continue

        try:
            checksum, rel = line.split("  ./", 1)
        except ValueError:
            return False

        expected[Path(rel)] = checksum

    actual = {}

    for path in fs.iter_files(root):
        rel = path.relative_to(root)

        if rel in exclude:
            continue

        actual[rel] = fs.sha256_file(path)

    return expected == actual


