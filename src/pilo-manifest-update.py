#!/usr/bin/env python3

import os
from pathlib import Path
import tempfile

import pilo


def update_subset(cx, name, root):
    manifest_dir = cx.admin_path / "manifest"
    manifest_file = manifest_dir / f"{name}.manifest"

    # generate manifest content
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        for line in pilo.generate_manifest_lines(root):
            tmp.write(line + "\n")

    # ensure git repo exists
    cx.ensure_git_repo(manifest_dir)

    # copy into place (as user)
    cx.copy(tmp_path, manifest_file)

    # commit if changed
    cx.git_commit_if_changed(
        manifest_dir,
        manifest_file,
        f"{name} manifest update"
    )

    tmp_path.unlink(missing_ok=True)


def main():
    cx = pilo.Context(os.environ)

    update_subset(cx, "pile", cx.pile_path)
    update_subset(cx, "collection", cx.static_path / "collection")
    update_subset(cx, "filing", cx.static_path / "filing")


if __name__ == "__main__":
    main()
