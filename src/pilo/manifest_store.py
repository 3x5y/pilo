from pathlib import Path
import shutil
import tempfile

from . import fs
from . import git

from .manifest_codec import (
    render_manifest_lines,
)

from .manifest_verify import (
    generate_manifest_entries,
)


def write_manifest_entries(cx, manifest_path, entries):

    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        for line in render_manifest_lines(entries):
            tmp.write(line + "\n")

    fs.ensure_parent_dir(cx, manifest_path)
    shutil.move(tmp_path, manifest_path)
    fs.ensure_owned(cx, manifest_path)
    manifest_path.chmod(0o644)


def write_manifest(cx, root: Path, manifest: Path):
    entries = list(generate_manifest_entries(root))
    write_manifest_entries(cx, manifest, entries)


def commit_manifest_if_changed(cx, manifest, message):
    repo = cx.admin_path / "manifest"
    git.ensure_repo(cx, repo)
    git.commit_if_changed(cx, repo, manifest, message)
