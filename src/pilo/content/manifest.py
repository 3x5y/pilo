from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile

from .. import error
from .. import fs


# --- data model ---

@dataclass(frozen=True)
class ManifestEntry:
    checksum: str
    path: Path


@dataclass(frozen=True)
class ManifestAddEntry:
    subset: str
    entry: ManifestEntry


@dataclass(frozen=True)
class ManifestRemoveEntry:
    subset: str
    path: Path


class ManifestIndex:

    def __init__(self, entries):
        self._entries = {}
        for entry in entries:
            self._entries[entry.path] = entry

    def lookup(self, path: Path):
        return self._entries.get(path)

    def require(self, path: Path):
        entry = self.lookup(path)
        if entry is None:
            error.fatal(f"manifest entry missing: {path}")
        return entry


def as_manifest_index(entries):
    if isinstance(entries, ManifestIndex):
        return entries
    return ManifestIndex(entries)


# --- codec ---

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


# --- policy / domain ---

MANIFEST_DATASET_PATTERNS = {
    "pile": "/pile",
    "collection": "/static/collection",
    "filing": "/static/filing",
}


def dataset_manifest_subset(dataset):
    if dataset.endswith(MANIFEST_DATASET_PATTERNS["pile"]):
        return "pile"
    for subset in ("collection", "filing"):
        pattern = MANIFEST_DATASET_PATTERNS[subset]
        if pattern in dataset:
            return subset
    return None


def build_addition(subset, path, checksum):
    entry = ManifestEntry(checksum=checksum, path=path)
    return ManifestAddEntry(subset=subset, entry=entry)


def build_removal(subset, path):
    return ManifestRemoveEntry(subset=subset, path=path)


# --- mutation / apply ---

def apply_manifest_mutations(entries, muts):
    by_path = {entry.path: entry for entry in entries}
    for mut in muts:
        if isinstance(mut, ManifestRemoveEntry):
            by_path.pop(mut.path, None)
        elif isinstance(mut, ManifestAddEntry):
            by_path[mut.entry.path] = mut.entry
    return [by_path[path] for path in sorted(by_path)]


def execute_manifest_mutations(cx, subset, manifest_path, muts):
    relevant = [mut for mut in muts if mut.subset == subset]
    entries = load_manifest_entries(manifest_path)
    updated = apply_manifest_mutations(entries, relevant)
    write_manifest_entries(cx, manifest_path, updated)


# --- store / persistence ---

def write_manifest_entries(cx, manifest_path, entries):
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        for line in render_manifest_lines(entries):
            tmp.write(line + "\n")
    fs.ensure_parent_dir(cx, manifest_path)
    shutil.move(tmp_path, manifest_path)
    fs.ensure_owned(cx, manifest_path)
    manifest_path.chmod(0o644)


# --- verify ---

def generate_manifest_entries(root: Path, exclude=None):
    exclude = set(exclude or [])
    for path in sorted(fs.iter_files(root)):
        rel = path.relative_to(root)
        if rel in exclude:
            continue
        checksum = fs.hash_file1(path)
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
        actual[rel] = fs.hash_file1(path)
    return expected == actual


def verify_checksum(path: Path, expected_checksum: str):
    actual = fs.hash_file1(path)
    if actual != expected_checksum:
        error.fatal(
            f"checksum verification failed: "
            f"{path}"
        )


# --- continuity / transfer ---

@dataclass(frozen=True)
class ContinuityMapping:
    src_subset: str
    dst_subset: str
    src: Path
    dst: Path
    checksum: str


def build_transfer_mutations(mappings):

    muts = []
    for m in mappings:
        muts.append(
            build_removal(
                m.src_subset,
                m.src,
            )
        )
        muts.append(
            build_addition(
                m.dst_subset,
                m.dst,
                m.checksum,
            )
        )
    return muts
