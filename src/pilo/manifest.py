from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile

from . import error
from . import fs
from . import git
from . import paths
from . import util


MANIFEST_SUBSET_DOMAINS = {
    "pile": paths.StorageDomain.PILE,
    "collection": paths.StorageDomain.COLLECTION,
    "filing": paths.StorageDomain.FILING,
}


MANIFEST_DATASET_PATTERNS = {
    "pile": "/pile",
    "collection": "/static/collection",
    "filing": "/static/filing",
}


@dataclass(frozen=True)
class ManifestSubset:
    name: str
    root: Path
    manifest: Path


@dataclass(frozen=True)
class ManifestUpdatePlan:
    subsets: list[ManifestSubset]


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


def manifest_subset_domain(subset):
    try:
        return MANIFEST_SUBSET_DOMAINS[subset]
    except KeyError:
        error.fatal(f"invalid manifest subset: {subset}")


def manifest_subset_root(cx, subset):
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


def generate_manifest_lines(root: Path, exclude=None):
    for entry in generate_manifest_entries(root, exclude):
        yield render_manifest_entry(entry)


def verify_manifest_lines(root: Path, lines, exclude=None):
    root = Path(root)
    exclude = set(exclude or [])

    for line in lines:
        line = line.strip()

        if not line:
            continue

        try:
            entry = parse_manifest_line(line)
        except ValueError:
            return False

        path = root / rel

        relpath = path.relative_to(root)
        if relpath in exclude:
            continue

        if not path.is_file():
            return False

        actual = fs.sha256_file(path)

        if actual != entry.checksum:
            return False

    return True


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


def build_manifest_update_plan(cx, subsets):
    def build(name):
        manifest = cx.admin_path / "manifest" / f"{name}.manifest"
        root = manifest_subset_root(cx, name)
        return ManifestSubset(name=name, root=root, manifest=manifest)

    resolved = [build(name) for name in subsets]
    return ManifestUpdatePlan(subsets=resolved)


def execute_manifest_update_plan(cx, plan):
    for subset in plan.subsets:
        fs.ensure_parent_dir(cx, subset.manifest)
        write_manifest(cx, subset.root, subset.manifest)
        msg = f"{subset.name} manifest update"
        commit_manifest_if_changed(cx, subset.manifest, msg)


def write_manifest(cx, root: Path, manifest: Path):

    entries = list(
        generate_manifest_entries(root)
    )

    write_manifest_entries(
        cx,
        manifest,
        entries,
    )


def commit_manifest_if_changed(cx, manifest, message):
    repo = cx.admin_path / "manifest"
    git.ensure_repo(cx, repo)
    git.commit_if_changed(cx, repo, manifest, message)


def render_manifest_entry(entry):
    return f"{entry.checksum}  ./{entry.path}"


def parse_manifest_line(line):
    try:
        checksum, rel = line.split("  ./", 1)
    except ValueError:
        raise ValueError(f"invalid manifest line: {line}")

    return ManifestEntry(checksum=checksum, path=Path(rel))


def generate_manifest_entries(root: Path, exclude=None):
    exclude = set(exclude or [])

    for path in sorted(fs.iter_files(root)):
        rel = path.relative_to(root)

        if rel in exclude:
            continue

        yield ManifestEntry(
            checksum=fs.sha256_file(path),
            path=rel,
        )


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


def apply_manifest_mutations(entries, muts):

    by_path = {
        entry.path: entry
        for entry in entries
    }

    for mut in muts:

        if isinstance(mut, ManifestRemoveEntry):
            by_path.pop(mut.path, None)

        elif isinstance(mut, ManifestAddEntry):
            by_path[mut.entry.path] = mut.entry

    return [
        by_path[path]
        for path in sorted(by_path)
    ]


def write_manifest_entries(cx, manifest_path, entries):

    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp_path = Path(tmp.name)

        for line in render_manifest_lines(entries):
            tmp.write(line + "\n")

    fs.ensure_parent_dir(cx, manifest_path)
    shutil.move(tmp_path, manifest_path)
    fs.ensure_owned(cx, manifest_path)
    manifest_path.chmod(0o644)


def execute_manifest_mutations(cx, subset, manifest_path, muts):
    relevant = [mut for mut in muts if mut.subset == subset]
    entries = load_manifest_entries(manifest_path)
    updated = apply_manifest_mutations(entries, relevant)
    write_manifest_entries(cx, manifest_path, updated)
