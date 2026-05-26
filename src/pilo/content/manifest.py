from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import shutil
import tempfile

from .. import error
from .. import fs
from .. import git
from .. import paths

from . import manifest



# --- data model (was manifest_model.py) ---

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


class ChecksumProvenance(Enum):
    MANIFEST = "manifest"
    VERIFIED = "verified"
    GENERATED = "generated"


@dataclass(frozen=True)
class ProvenancedChecksum:
    path: Path
    checksum: str
    provenance: ChecksumProvenance


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


class ChecksumIndex:

    def __init__(self, checksums):
        self._checksums = {}
        for item in checksums:
            normalized = as_provenanced_checksum(item)
            self._checksums[normalized.path] = normalized

    def lookup(self, path: Path):
        return self._checksums.get(path)

    def require(self, path: Path):
        item = self.lookup(path)
        if item is None:
            error.fatal(f"verified checksum missing: {path}")
        return item


def as_manifest_index(entries):
    if isinstance(entries, ManifestIndex):
        return entries
    return ManifestIndex(entries)


def as_checksum_index(items):
    if isinstance(items, ChecksumIndex):
        return items
    if isinstance(items, dict):
        items = items.values()
    return ChecksumIndex(items)


def as_provenanced_checksum(item):
    if isinstance(item, ProvenancedChecksum):
        return item
    if isinstance(item, ManifestEntry):
        return ProvenancedChecksum(
            path=item.path,
            checksum=item.checksum,
            provenance=ChecksumProvenance.MANIFEST,
        )
    error.fatal(f"unsupported checksum item: {type(item).__name__}")


# --- codec (was manifest_codec.py) ---

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


# --- policy / domain (was manifest_policy.py) ---

# unused
__MANIFEST_SUBSET_DOMAINS = {
    "pile": paths.StorageDomain.PILE,
    "collection": paths.StorageDomain.COLLECTION,
    "filing": paths.StorageDomain.FILING,
}

MANIFEST_DATASET_PATTERNS = {
    "pile": "/pile",
    "collection": "/static/collection",
    "filing": "/static/filing",
}


def __manifest_subset_domain(subset):
    try:
        return MANIFEST_SUBSET_DOMAINS[subset]
    except KeyError:
        error.fatal(f"invalid manifest subset: {subset}")


def __manifest_subset_root(cx, subset):
    domain = manifest_subset_domain(subset)
    policy = cx.storage_policy(domain)
    return policy.root_path


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


def build_pile_additions(paths, checksums):
    index = as_checksum_index(checksums)
    muts = []
    for rel in paths:
        item = index.require(rel)
        add = build_addition("pile", rel, item.checksum)
        muts.append(add)
    return muts


# --- mutation / apply (was manifest_mutation.py) ---

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
    msg = f"{subset} manifest update"
    commit_manifest_if_changed(cx, manifest_path, msg)


# --- store / persistence (was manifest_store.py) ---

def write_manifest_entries(cx, manifest_path, entries):
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        for line in render_manifest_lines(entries):
            tmp.write(line + "\n")
    fs.ensure_parent_dir(cx, manifest_path)
    shutil.move(tmp_path, manifest_path)
    fs.ensure_owned(cx, manifest_path)
    manifest_path.chmod(0o644)


def commit_manifest_if_changed(cx, manifest, message):
    repo = cx.admin_path / "manifest"
    git.ensure_repo(cx, repo)
    git.commit_if_changed(cx, repo, manifest, message)


# --- verify (was manifest_verify.py) ---

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


def generate_checksum(path: Path):
    checksum = fs.hash_file1(path)
    return (
        ProvenancedChecksum(
            path=path,
            checksum=checksum,
            provenance=(
                ChecksumProvenance
                .GENERATED
            ),
        )
    )


def verify_checksum(path: Path, expected_checksum: str):
    actual = fs.hash_file1(path)
    if actual != expected_checksum:
        error.fatal(
            f"checksum verification failed: "
            f"{path}"
        )
    return (
        ProvenancedChecksum(
            path=path,
            checksum=expected_checksum,
            provenance=(
                ChecksumProvenance
                .VERIFIED
            ),
        )
    )


# unused
def reuse_manifest_checksum(entry):
    return (
        ProvenancedChecksum(
            path=entry.path,
            checksum=entry.checksum,
            provenance=(
                ChecksumProvenance
                .MANIFEST
            ),
        )
    )


@dataclass(frozen=True)
class ContinuityMapping:
    src_subset: str
    dst_subset: str
    src: Path
    dst: Path


@dataclass(frozen=True)
class ContinuityTransfer:
    src_subset: str
    dst_subset: str
    src: Path
    dst: Path
    checksum: str
    provenance: manifest.ChecksumProvenance


@dataclass(frozen=True)
class ContinuityRemoval:
    subset: str
    path: Path


def build_transfer_mutations(mappings, verified):
    transfers = build_transfers(mappings, verified)
    return build_mutations(transfers)


def build_removal_mutations(removals):
    muts = []
    for removal in removals:
        muts.append(
            manifest.build_removal(
                removal.subset,
                removal.path,
            )
        )
    return muts


def build_transfers(mappings, verified):

    verified = manifest.as_checksum_index(verified)
    transfers = []

    for m in mappings:
        item = verified.require(m.src)
        transfers.append(
            ContinuityTransfer(
                src_subset=m.src_subset,
                dst_subset=m.dst_subset,
                src=m.src,
                dst=m.dst,
                checksum=item.checksum,
                provenance=item.provenance,
            )
        )
    return transfers


def build_mutations(transfers):

    muts = []
    for transfer in transfers:
        muts.append(
            manifest.build_removal(
                transfer.src_subset,
                transfer.src,
            )
        )
        muts.append(
            manifest.build_addition(
                transfer.dst_subset,
                transfer.dst,
                transfer.checksum,
            )
        )
    return muts


def acquire_verified_checksums(paths, entries):

    index = manifest.as_manifest_index(entries)
    verified = []

    for rel_path, real_path in paths:
        existing = index.require(rel_path)
        verified_item = manifest.verify_checksum(real_path, existing.checksum)
        verified.append(
            manifest.ProvenancedChecksum(
                path=rel_path,
                checksum=verified_item.checksum,
                provenance=verified_item.provenance,
            )
        )
    return manifest.ChecksumIndex(verified)


def acquire_generated_checksums(paths):

    generated = []
    for rel_path, real_path in paths:
        item = manifest.generate_checksum(real_path)
        generated.append(
            manifest.ProvenancedChecksum(
                path=rel_path,
                checksum=item.checksum,
                provenance=item.provenance,
            )
        )
    return manifest.ChecksumIndex(generated)


# --- updates -- unused

@dataclass(frozen=True)
class __ManifestSubset:
    name: str
    root: Path
    manifest: Path


@dataclass(frozen=True)
class __ManifestUpdatePlan:
    subsets: list[ManifestSubset]


def __write_manifest(cx, root: Path, manifest: Path):
    entries = list(generate_manifest_entries(root))
    write_manifest_entries(cx, manifest, entries)


def __build_manifest_update_plan(cx, subsets):
    def build(name):
        manifest = cx.admin_path / "manifest" / f"{name}.manifest"
        root = manifest_subset_root(cx, name)
        return ManifestSubset(name=name, root=root, manifest=manifest)
    resolved = [build(name) for name in subsets]
    return ManifestUpdatePlan(subsets=resolved)


def __execute_manifest_update_plan(cx, plan):
    for subset in plan.subsets:
        fs.ensure_parent_dir(cx, subset.manifest)
        write_manifest(cx, subset.root, subset.manifest)
        msg = f"{subset.name} manifest update"
        commit_manifest_if_changed(cx, subset.manifest, msg)
