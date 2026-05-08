from dataclasses import dataclass
from pathlib import Path
import subprocess

from .. import error
from ..manifest import manifest_subset_root


@dataclass(frozen=True)
class ManifestVerifyOp:
    subset: str
    root: Path
    manifest: Path


def build_manifest_verify_plan(cx, subsets):
    def build(subset):
        m = cx.admin_path / "manifest" / f"{subset}.manifest"
        return ManifestVerifyOp(subset=subset,
                                root=manifest_subset_root(cx, subset),
                                manifest=m)
    return [build(subset) for subset in subsets]


def verify_manifest_op(op):
    m = op.manifest
    if not m.is_file() or m.stat().st_size == 0:
        return
    cmd = ["sha256sum", "--quiet", "--strict", "-c", m]
    try:
        subprocess.run(cmd, cwd=op.root, check=True)
    except subprocess.CalledProcessError:
        error.fatal(f"manifest verification failed: {op.subset}")


def execute_manifest_verify_plan(ops):
    for op in ops:
        verify_manifest_op(op)