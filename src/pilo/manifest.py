from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile

from . import error
from . import fs
from . import util


@dataclass(frozen=True)
class ManifestSubset:
    name: str
    root: Path
    manifest: Path


@dataclass(frozen=True)
class ManifestUpdatePlan:
    subsets: list[ManifestSubset]


def manifest_subset_root(cx, subset):
    if subset == "pile":
        return cx.pile_path
    if subset == "collection":
        return cx.static_path / "collection"
    if subset == "filing":
        return cx.static_path / "filing"
    error.fatal(f"invalid manifest subset: {subset}")


def generate_manifest_lines(root: Path):
    for path in sorted(fs.iter_files(root)):
        rel = path.relative_to(root)
        h = fs.sha256_file(path)
        yield f"{h}  ./{rel}"


def verify_manifest_lines(root: Path, lines):
    root = Path(root)

    for line in lines:
        line = line.strip()

        if not line:
            continue

        try:
            expected, rel = line.split("  ./", 1)
        except ValueError:
            return False

        path = root / rel

        if not path.is_file():
            return False

        actual = fs.sha256_file(path)

        if actual != expected:
            return False

    return True


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
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        for line in generate_manifest_lines(root):
            tmp.write(line + "\n")

    fs.ensure_parent_dir(cx, manifest)
    shutil.move(tmp_path, manifest)
    fs.ensure_owned(cx, manifest)
    manifest.chmod(0o644)


def commit_manifest_if_changed(cx, manifest, message):
    repo = cx.admin_path / "manifest"
    util.ensure_git_repo(cx, repo)
    util.git_commit_if_changed(cx, repo, manifest, message)
