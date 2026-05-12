from pathlib import Path

from .manifest_model import ManifestEntry


def render_manifest_entry(entry):
    return f"{entry.checksum}  ./{entry.path}"


def parse_manifest_line(line):
    try:
        checksum, rel = line.split("  ./", 1)
    except ValueError:
        raise ValueError(f"invalid manifest line: {line}")
    return ManifestEntry(checksum=checksum, path=Path(rel))


def render_manifest_lines(entries):
    for entry in entries:
        yield render_manifest_entry(entry)


def load_manifest_entries(path):
    entries = []

    if not path.exists():
        return entries

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        entries.append(parse_manifest_line(line))

    return entries


def find_manifest_entry(entries, path):
    for entry in entries:
        if entry.path == path:
            return entry
    return None
