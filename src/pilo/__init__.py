import filecmp
import hashlib
import os
import pwd
import shutil
import subprocess
import sys
import tempfile
from contextlib import ExitStack
from datetime import datetime
from enum import Enum

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from . import zfs


def fatal(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd, check=True):
    return subprocess.run(cmd, check=check)


def require_dataset(dataset):
    if not zfs.dataset_exists(dataset):
        fatal(f"missing required dataset: {dataset}")


def require_new_dataset(dataset):
    if zfs.dataset_exists(dataset):
        fatal(f"destination exists: {dataset}")


def require_snapshot(snapshot):
    if not zfs.snapshot_exists(snapshot):
        fatal(f"missing snapshot: {snapshot}")


def require_snapshot_of_dataset(snap, dataset):
    require_snapshot(snap)
    if not snap.startswith(dataset + "@"):
        fatal(f"snapshot {snap} does not belong to {dataset}")


def require_within_dataset(target, root):
    if not target == root and not target.startswith(root + "/"):
        fatal(f"{target} outside {root}")


class validate:
    @staticmethod
    def dataset_exists(ds):
        require_dataset(ds)

    @staticmethod
    def snapshot_exists(snap):
        require_snapshot(snap)

    @staticmethod
    def new_dataset(ds):
        require_new_dataset(ds)


#####################
#    init stuff     #
#####################


def apply_dataset_contract(cx):

    apply_namespace(cx.root_dataset + '/active')
    apply_filesystem(cx.root_dataset + '/active/admin',
                     readonly=False,
                     mountpoint=cx.admin_path)
    apply_filesystem(cx.root_dataset + '/active/pile-intake',
                     readonly=False,
                     mountpoint=cx.intake_path)
    apply_filesystem(cx.root_dataset + '/active/pile-readonly',
                     readonly=True,
                     mountpoint=cx.pile_path)

    apply_namespace(cx.root_dataset + '/static')
    apply_filesystem(cx.root_dataset + '/static/collection',
                     readonly=True,
                     mountpoint=cx.collection_path)

    apply_namespace(cx.root_dataset + '/static/filing',
                    mountpoint=cx.filing_path)


def apply_namespace(ds, mountpoint=None):
    require_dataset(ds)
    mp = zfs.get_prop(ds, 'mountpoint')
    if mountpoint and mp != str(mountpoint):
        zfs.set_prop(ds, f"mountpoint={mountpoint}")
    zfs.set_prop(ds, "canmount=off")


def apply_filesystem(ds, mountpoint, readonly):
    require_dataset(ds)
    zfs.set_readonly(ds, readonly)
    mp = zfs.get_prop(ds, 'mountpoint')
    if mp != str(mountpoint):
        zfs.set_prop(ds, f"mountpoint={mountpoint}")
    zfs.set_prop(ds, "canmount=on")


def ensure_runtime_dirs(cx):
    pile = cx.pile_path
    with dataset_writable(cx.pile_dataset):
        cx.ensure_dir(pile / "in")
        cx.ensure_dir(pile / "sort")
        cx.ensure_dir(pile / "out")
        cx.ensure_dir(pile / "out" / "collection")
        cx.ensure_dir(pile / "out" / "filing")


def apply_ownership(cx):
    cx.ensure_owned(cx.admin_path)
    cx.ensure_owned(cx.intake_path)
    with dataset_writable(cx.pile_dataset):
        cx.ensure_owned(cx.pile_path)
    with dataset_writable(cx.collection_dataset):
        cx.ensure_owned(cx.collection_path)


#####################
# static file stuff #
#####################


def generate_manifest_lines(root: Path):
    for path in sorted(iter_files(root)):
        rel = path.relative_to(root)
        h = sha256_file(path)
        yield f"{h}  ./{rel}"


@contextmanager
def dataset_writable(dataset):
    was = zfs.get_readonly(dataset)
    if was:
        zfs.set_readonly(dataset, False)
    try:
        yield
    finally:
        if was:
            zfs.set_readonly(dataset, True)


def list_files(root):
    return sorted(iter_files(root))


def iter_files(root):
    root = Path(root)
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def ensure_parent_dir(cx, path: Path):
    ensure_dir_owned(cx, path.parent)


def ensure_dir_owned(cx, path: Path):
    path = Path(path)

    missing = []

    cur = path

    while not cur.exists():
        missing.append(cur)
        cur = cur.parent

    path.mkdir(parents=True, exist_ok=True)

    for d in reversed(missing):
        cx.ensure_owned(d)


def safe_copy(cx, src: Path, dst: Path):
    ensure_parent_dir(cx, dst)
    cx.ensure_owned(dst.parent)
    shutil.copy2(src, dst)
    cx.ensure_owned(dst)


def safe_move(cx, src: Path, dst: Path):
    ensure_parent_dir(cx, dst)
    cx.ensure_owned(dst.parent)
    shutil.move(src, dst)
    cx.ensure_owned(dst)


def safe_unlink(path: Path):
    path.unlink()


def files_equal(a, b):
    return filecmp.cmp(a, b, shallow=False)


def domain(rel: Path):
    parts = rel.parts
    if not parts:
        return "invalid"

    if parts[0] in ("in", "out", "sort"):
        return "pile"
    if parts[0] in ("collection", "filing"):
        return "static"
    return "invalid"


class StorageDomain(Enum):
    PILE = "pile"
    COLLECTION = "collection"
    FILING = "filing"


@dataclass(frozen=True)
class LogicalPath:
    domain: StorageDomain
    relpath: Path


@dataclass(frozen=True)
class ResolvedPath:
    logical: LogicalPath
    physical: Path
    dataset: str
    @property
    def path(self):
        return self.physical


@dataclass
class Resolved:
    path: Path
    dataset: str


def parse_logical_path(path: Path) -> LogicalPath:
    if not path.parts:
        fatal("empty path")

    if path.is_absolute():
        fatal("absolute paths not allowed")

    if ".." in path.parts:
        fatal("parent traversal not allowed")

    top = path.parts[0]

    if top in ("in", "out", "sort"):
        return LogicalPath(
            domain=StorageDomain.PILE,
            relpath=path,
        )

    if top == "collection":
        if len(path.parts) < 2:
            fatal("invalid collection path")

        return LogicalPath(
            domain=StorageDomain.COLLECTION,
            relpath=Path(*path.parts[1:]),
        )

    if top == "filing":
        if len(path.parts) < 3:
            fatal("invalid filing path")

        return LogicalPath(
            domain=StorageDomain.FILING,
            relpath=Path(*path.parts[1:]),
        )

    fatal(f"invalid path: {path}")


class Context:
    def __init__(self, environ=os.environ, args=sys.argv):
        self.root_dataset = environ["PILO_ROOT"]
        self.replica_dataset = environ["PILO_REPLICA_ROOT"]
        self.admin_dataset = environ["PILO_ADMIN_DATASET"]
        self.intake_dataset = environ["PILO_INTAKE_DATASET"]
        self.pile_dataset = environ["PILO_PILE_DATASET"]
        self.static_dataset = environ["PILO_STATIC_DATASET"]
        self.collection_dataset = f"{self.static_dataset}/collection"
        self.filing_dataset = f"{self.static_dataset}/filing"

        self.path = Path(environ["PILO_PATH"])
        self.admin_path = Path(environ["PILO_ADMIN_PATH"])
        self.intake_path = Path(environ["PILO_INTAKE_PATH"])
        self.pile_path = Path(environ["PILO_PILE_PATH"])
        self.static_path = Path(environ["PILO_STATIC_PATH"])
        #self.collection_path = Path(environ["PILO_COLLECTION_PATH"])
        #self.filing_path = Path(environ["PILO_FILING_PATH"])
        self.collection_path = self.static_path / 'collection'
        self.filing_path = self.static_path / 'filing'

        self.user = environ["PILO_USER"]
        self.user_id = pwd.getpwnam(self.user).pw_uid
        self.args = args and args[1:] or []

    def resolve(self, rel: Path) -> ResolvedPath:
        logical = parse_logical_path(rel)

        if logical.domain == StorageDomain.PILE:
            return ResolvedPath(
                logical=logical,
                physical=self.pile_path / logical.relpath,
                dataset=self.pile_dataset,
            )

        if logical.domain == StorageDomain.COLLECTION:
            return ResolvedPath(
                logical=logical,
                physical=self.collection_path / logical.relpath,
                dataset=self.collection_dataset,
            )

        if logical.domain == StorageDomain.FILING:
            subset = logical.relpath.parts[0]

            return ResolvedPath(
                logical=logical,
                physical=self.filing_path / logical.relpath,
                dataset=f"{self.filing_dataset}/{subset}",
            )

        raise AssertionError("unreachable")

    def as_user(self, cmd, check=True, **kw):
        if os.geteuid() == 0:
            return subprocess.run(["sudo", "-u", self.user] + cmd,
                                  check=check,
                                  **kw)
        else:
            return subprocess.run(cmd, check=check, **kw)

    def ensure_owned(self, path):
        stat = os.stat(path)
        if not stat.st_uid == stat.st_gid == self.user_id:
            shutil.chown(path, self.user, self.user)

    def ensure_dir(self, path):
        ensure_dir_owned(self, path)

    def move(self, src, dst):
        safe_move(self, src, dst)

    def copy(self, src, dst):
        safe_copy(self, src, dst)

    def copy_static(self, src, resolved):
        with dataset_writable(resolved.dataset):
            self.copy(src, resolved.path)

    def remove_piled(self, path):
        with dataset_writable(self.pile_dataset):
            safe_unlink(path)

    def ensure_git_repo(self, path: Path):
        git_path = path / ".git"
        if not git_path.is_dir():
            self.ensure_dir(path)
            cmd = ["git", "-c", "init.defaultBranch=master", "init", str(path)]
            self.as_user(cmd, capture_output=True)

    def git_commit_if_changed(self, repo: Path, file: Path, message: str):
        cmd = ["git", "-C", str(repo), "add", str(file)]
        self.as_user(cmd)

        cmd = ["git", "-C", str(repo), "diff", "--quiet", "--cached"]
        result = self.as_user(cmd, check=False)

        if result.returncode != 0:
            cmd = [ "git", "-C", str(repo), "commit", "-m", message]
            self.as_user(cmd, capture_output=True)


#####################
# replication stuff #
#####################


class ReplicationStatus(Enum):
    OK = "OK"
    EMPTY = "EMPTY"
    BEHIND = "BEHIND"
    DIVERGED = "DIVERGED"
    UNKNOWN = "UNKNOWN"


def _find_incremental_base(src, dst):
    guid = zfs.get_latest_guid(dst)
    if not guid:
        return None
    for name, g in zfs.snapshot_guids(src):
        if g == guid:
            return name
    return None


def snapshot_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def replicate(src, dst):
    plan = build_replication_plan(src, dst)
    return execute_replication_plan(plan)


def replication_status(src, dst):
    src_guid = zfs.get_latest_guid(src)
    dst_guid = zfs.get_latest_guid(dst)

    if not dst_guid:
        return ReplicationStatus.EMPTY, "no snapshots on target"

    mapping = DatasetMapping(src, dst)

    for dst_ds in zfs.list_filesystems(dst):
        src_ds = mapping.inverse(dst_ds)

        src_guids = set(zfs.list_guids(src_ds))
        dst_guids = set(zfs.list_guids(dst_ds))

        if dst_guids - src_guids:
            return ReplicationStatus.DIVERGED, f"divergence in {dst_ds}"

        if zfs.get_latest_guid(src_ds) != zfs.get_latest_guid(dst_ds):
            return ReplicationStatus.BEHIND, f"behind in {dst_ds}"

    for src_ds in zfs.list_filesystems(src):
        dst_ds = mapping.map(src_ds)
        if not zfs.dataset_exists(dst_ds):
            return ReplicationStatus.BEHIND, f"missing {dst_ds}"

    if src_guid != dst_guid:
        return ReplicationStatus.UNKNOWN, "root GUID mismatch"

    return ReplicationStatus.OK, None


################
# status stuff #
################


def now_epoch():
    return int(datetime.now().timestamp())


def git_dirty(repo: Path):
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--quiet"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode != 0




#####################
#   restore stuff   #
#####################


def restore_dataset(src_snap, dst, recursive=False, require_new=True):
    require_snapshot(src_snap)

    if require_new:
        require_new_dataset(dst)

    zfs.send_recv(src_snap, dst, recursive=recursive)

    snap_name = src_snap.split("@", 1)[1]
    if not zfs.snapshot_exists(f"{dst}@{snap_name}"):
        fatal("restore completed but snapshot missing at destination")


def restore_from_snapshot(src, dst, snap, recursive):
    src_snap = f"{src}@{snap}"
    restore_dataset(src_snap, dst, recursive=recursive)


def recover_dataset_tree(cx, target, replica, require_new=True):
    plan = build_recovery_plan(cx, target)
    execute_recovery_plan(plan)

    # normalise dataset properties
    apply_dataset_contract(cx)

    # ensure datasets are mountable and mounted
    zfs.mount()

    # Optional: runtime + ownership (debatable)
    #ensure_runtime_dirs(cx)
    #apply_ownership(cx)


@dataclass(frozen=True)
class DatasetMapping:
    src_root: str
    dst_root: str

    def _suffix(self, dataset: str, root: str) -> str:
        if not dataset.startswith(root):
            fatal(f"dataset outside root: {dataset}")
        return dataset[len(root):].lstrip("/")

    def map(self, dataset: str) -> str:
        suffix = self._suffix(dataset, self.src_root)
        return f"{self.dst_root}/{suffix}" if suffix else self.dst_root

    def inverse(self, dataset: str) -> str:
        suffix = self._suffix(dataset, self.dst_root)
        return f"{self.src_root}/{suffix}" if suffix else self.src_root

    def validate_within_src(self, dataset: str):
        if not dataset.startswith(self.src_root):
            fatal(f"target outside source root: {dataset}")

    def validate_within_dst(self, dataset: str):
        if not dataset.startswith(self.dst_root):
            fatal(f"target outside destination root: {dataset}")


@dataclass(frozen=True)
class RecoveryPlan:
    target: str
    replica: str
    snapshot: str
    recursive: bool


def build_recovery_plan(cx, target):
    mapping = DatasetMapping(cx.root_dataset, cx.replica_dataset)

    #mapping.validate_within_src(target)
    require_within_dataset(target, cx.root_dataset)

    replica = mapping.map(target)
    require_dataset(replica)

    snap = zfs.latest_snapshot(replica)
    if not snap:
        fatal("no snapshots on replica")

    require_snapshot_of_dataset(snap, replica)

    require_new_dataset(target)

    return RecoveryPlan(
        target=target,
        replica=replica,
        snapshot=snap,
        recursive=True,
    )


def execute_recovery_plan(plan: RecoveryPlan, cx):
    restore_dataset(
        plan.snapshot,
        plan.target,
        recursive=plan.recursive,
    )
    normalize_system(cx)


@dataclass(frozen=True)
class RestorePlan:
    src_snapshot: str
    dst: str
    recursive: bool


def build_restore_plan(src, dst, snap, recursive):
    if "@" in snap:
        fatal("snapshot must not include dataset")

    src_snap = f"{src}@{snap}"

    require_snapshot(src_snap)
    require_snapshot_of_dataset(src_snap, src)
    require_new_dataset(dst)

    return RestorePlan(
        src_snapshot=src_snap,
        dst=dst,
        recursive=recursive,
    )


def execute_restore_plan(plan: RestorePlan):
    restore_dataset(
        plan.src_snapshot,
        plan.dst,
        recursive=plan.recursive,
    )


def normalize_system(cx):
    apply_dataset_contract(cx)
    zfs.mount()
    ensure_runtime_dirs(cx)
    apply_ownership(cx)


@dataclass(frozen=True)
class ReplicationPlan:
    src: str
    dst: str
    snapshot: str
    base: str | None
    mode: str  # "full" | "incremental" | "noop"


def build_replication_plan(src, dst):
    last_src = zfs.latest_snapshot(src)
    last_dst = zfs.latest_snapshot(dst)

    if not last_src:
        fatal("no source snapshot")

    # if strict (need to change test mocks)
    #require_dataset(src)
    if not last_dst:
        return ReplicationPlan( src, dst, last_src, None, "full")

    base = _find_incremental_base(src, dst)

    if not base:
        fatal(f"base snapshot missing on source: {base}")

    if base == last_src:
        return ReplicationPlan(src, dst, last_src, base, "noop")

    return ReplicationPlan(src, dst, last_src, base, "incremental")


def execute_replication_plan(plan: ReplicationPlan):
    if plan.mode == "full":
        return zfs.replicate_full(plan.snapshot, plan.dst)

    if plan.mode == "incremental":
        return zfs.replicate_incremental(plan.base, plan.snapshot, plan.dst)

    if plan.mode == "noop":
        return


@dataclass
class SystemStatus:
    messages: list[str] = None
    code: int = 0

    def __post_init__(self):
        if self.messages is None:
            self.messages = []

    def warn(self, msg):
        self.messages.append(("WARN", msg))
        self.code = 1

    def ok(self, msg):
        self.messages.append(("OK", msg))


def check_replication_status(cx, st: SystemStatus):
    src = cx.root_dataset
    dst = cx.replica_dataset

    src_snap = zfs.latest_snapshot(src)
    dst_snap = zfs.latest_snapshot(dst)

    src_name = src_snap.split("@", 1)[1] if src_snap else "**MISSING**"
    dst_name = dst_snap.split("@", 1)[1] if dst_snap else "**MISSING**"

    if src_name != dst_name:
        st.warn(f"replication: latest={src_name} replicated={dst_name}")
    else:
        st.ok(f"replication: {src_name}")


def check_snapshot_status(cx, st: SystemStatus, max_age=None):
    dataset = cx.pile_dataset

    name, ts = zfs.latest_snapshot_with_time(dataset)
    if max_age is None:
        max_age = int(os.environ.get("CONFIG_SNAPSHOT_MAX_AGE", "3600"))

    if not name:
        st.warn(f"snapshot: none for {dataset}")
        return

    if ts is None:
        st.warn("snapshot: could not parse timestamp")
        return

    age = now_epoch() - ts

    if age > max_age:
        st.warn(f"snapshot: stale ({age} s)")
    else:
        st.ok(f"snapshot: fresh ({age} s)")


def check_dataset_status(cx, st: SystemStatus):
    required = [
        cx.admin_dataset,
        cx.intake_dataset,
        cx.pile_dataset,
        f"{cx.static_dataset}/collection",
    ]

    for ds in required:
        if not zfs.dataset_exists(ds):
            st.warn(f"incomplete: missing dataset {ds}")


def check_transient_status(cx, st: SystemStatus):
    for git_dir in cx.admin_path.rglob(".git"):
        repo = git_dir.parent
        if git_dirty(repo):
            st.warn(f"transient: repo {repo} has uncommitted changes")


def check_pile_status(cx, st: SystemStatus):
    pile = cx.pile_path
    if not pile.exists():
        return

    now = now_epoch()
    max_age = int(os.environ.get("CONFIG_PILE_MAX_AGE", "86400"))

    for f in iter_files(pile):
        age = now - int(f.stat().st_mtime)
        if age > max_age:
            st.warn(f"pile: {f} is older than threshold")


def collect_system_status(cx, check=None):
    st = SystemStatus()

    checks = {
        "transient": check_transient_status,
        "pile": check_pile_status,
        "snapshot": check_snapshot_status,
        "replication": check_replication_status,
        "datasets": check_dataset_status,
    }

    for name, fn in checks.items():
        if check is None or check == name:
            fn(cx, st)

    return st


@dataclass(frozen=True)
class SnapshotPolicy:
    prefix: str
    hold: bool = False
    raw: bool = False

    def build_name(self, ts: str) -> str:
        if self.raw:
            return self.prefix
        return f"{self.prefix}-{ts}"


def create_snapshot_with_policy(policy: SnapshotPolicy, dataset: str, ts=None):
    if not dataset:
        fatal("dataset required for snapshot")

    ts = ts or snapshot_timestamp()
    name = policy.build_name(ts)

    zfs.snapshot(name, dataset)
    snap = f"{dataset}@{name}"

    if policy.hold:
        zfs.hold("repl-anchor", snap)

    return snap


def create_prefixed_snapshot(prefix, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]
    policy = SnapshotPolicy(prefix=prefix)
    return create_snapshot_with_policy(policy, dataset)


def create_anchor(anchor_type, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]

    if anchor_type == "daily":
        policy = SnapshotPolicy(prefix="daily", hold=False)
    elif anchor_type == "rotation":
        policy = SnapshotPolicy(prefix="rotation", hold=True)
    else:
        fatal("invalid anchor type")

    return create_snapshot_with_policy(policy, dataset)


def create_snapshot(name, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]
    policy = SnapshotPolicy(prefix=name, raw=True)
    return create_snapshot_with_policy(policy, dataset, ts="")


def sha256_file(path: Path, chunk_size=1024 * 1024):
    h = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


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

        actual = sha256_file(path)

        if actual != expected:
            return False

    return True


@dataclass(frozen=True)
class RewriteOp:
    kind: str
    src: Path
    dst: Path


def validate_relative_path(path: Path):
    if path.is_absolute():
        fatal("absolute paths not allowed")

    if ".." in path.parts:
        fatal("parent traversal not allowed")

def parse_rewrite_ops(lines):
    ops = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        parts = line.split("\t")

        if len(parts) != 3:
            fatal(f"invalid command: {line}")

        kind, src, dst = parts

        if kind != "mv":
            fatal(f"unsupported operation: '{kind}'")

        src_p = Path(src)
        dst_p = Path(dst)

        validate_relative_path(src_p)
        validate_relative_path(dst_p)

        ops.append(
            RewriteOp(
                kind=kind,
                src=src_p,
                dst=dst_p,
            )
        )

    return ops


@dataclass(frozen=True)
class ResolvedRewriteOp:
    op: RewriteOp
    src: Resolved
    dst: Resolved


def resolve_rewrite_op(cx, op: RewriteOp):
    return ResolvedRewriteOp(
        op=op,
        src=cx.resolve(op.src),
        dst=cx.resolve(op.dst),
    )


def validate_rewrite_op(cx, op: ResolvedRewriteOp):
    src_domain = domain(op.op.src)
    dst_domain = domain(op.op.dst)

    if src_domain != dst_domain:
        fatal("cross-domain move not allowed")

    src_abs = op.src.path
    dst_abs = op.dst.path

    if not src_abs.is_file():
        fatal(f"source missing: {op.src}")

    if dst_abs.is_file() and not files_equal(src_abs, dst_abs):
        fatal(f"destination conflict: {op.dst}")


def validate_rewrite_ops(cx, ops):
    seen_src = set()
    seen_dst = set()

    for op in ops:

        if op.op.src in seen_src:
            fatal(f"duplicate source in script: {op.op.src}")

        if op.op.dst in seen_dst:
            fatal(f"destination conflict in script: {op.op.dst}")

        seen_src.add(op.op.src)
        seen_dst.add(op.op.dst)

        validate_rewrite_op(cx, op)


@dataclass(frozen=True)
class RewritePlan:
    ops: list[ResolvedRewriteOp]


def build_rewrite_plan(cx, ops):
    resolved = [
        resolve_rewrite_op(cx, op)
        for op in ops
    ]

    validate_rewrite_ops(cx, resolved)

    return RewritePlan(
        ops=resolved,
    )


def execute_rewrite_plan(cx, plan: RewritePlan):
    datasets = [
        op.src.dataset
        for op in plan.ops
    ]

    with writable_datasets(datasets):
        for op in plan.ops:
            apply_rewrite_op(cx, op)


def apply_rewrite_op(cx, op: ResolvedRewriteOp):
    src_abs = op.src.path
    dst_abs = op.dst.path

    if dst_abs.exists():
        safe_unlink(src_abs)
    else:
        safe_move(cx, src_abs, dst_abs)


@contextmanager
def writable_datasets(datasets):
    seen = []
    for ds in datasets:
        if ds not in seen:
            seen.append(ds)

    with ExitStack() as stack:
        for ds in seen:
            stack.enter_context(dataset_writable(ds))
        yield


def manifest_subset_root(cx, subset):
    if subset == "pile":
        return cx.pile_path

    if subset == "collection":
        return cx.static_path / "collection"

    if subset == "filing":
        return cx.static_path / "filing"

    fatal(f"invalid manifest subset: {subset}")


@dataclass(frozen=True)
class ManifestSubset:
    name: str
    root: Path
    manifest: Path


@dataclass(frozen=True)
class ManifestUpdatePlan:
    subsets: list[ManifestSubset]


def build_manifest_update_plan(cx, subsets):
    resolved = []

    for name in subsets:
        resolved.append(
            ManifestSubset(
                name=name,
                root=manifest_subset_root(cx, name),
                manifest=(
                    cx.admin_path
                    / "manifest"
                    / f"{name}.manifest"
                ),
            )
        )

    return ManifestUpdatePlan(
        subsets=resolved
    )


def execute_manifest_update_plan(cx, plan):
    for subset in plan.subsets:
        ensure_parent_dir(cx, subset.manifest)
        write_manifest(cx, subset.root, subset.manifest)

        commit_manifest_if_changed(
            cx,
            subset.manifest,
            f"{subset.name} manifest update",
        )


def write_manifest(cx, root: Path, manifest: Path):
    with tempfile.NamedTemporaryFile(
        "w",
        delete=False,
    ) as tmp:

        tmp_path = Path(tmp.name)

        for line in generate_manifest_lines(root):
            tmp.write(line + "\n")

    ensure_parent_dir(cx, manifest)
    shutil.move(tmp_path, manifest)
    cx.ensure_owned(manifest)
    manifest.chmod(0o644)


def commit_manifest_if_changed(
    cx,
    manifest,
    message,
):
    repo = cx.admin_path / "manifest"

    cx.ensure_git_repo(repo)

    cx.git_commit_if_changed(
        repo,
        manifest,
        message,
    )


@dataclass(frozen=True)
class IngestOp:
    src: Path
    dst: Path
    action: str


def build_ingest_ops(cx, files):
    ops = []
    for src in files:
        rel = src.relative_to(cx.intake_path)
        dst = cx.pile_path / "in" / rel
        if dst.exists():
            if files_equal(src, dst):
                action = 'noop'
            else:
                fatal(f"name collision with different content: '{rel}'")
        else:
            action = 'move'
        ops.append(IngestOp(src, dst, action))
    return ops


def execute_ingest_ops(cx, ops):
    with dataset_writable(cx.pile_dataset):
        for op in ops:
            if op.action == 'move':
                safe_move(cx, op.src, op.dst)
            elif op.action == 'noop':
                op.src.unlink()


@dataclass(frozen=True)
class PromoteOp:
    src: Path
    dst: Path
    dataset: str
    action: str


def build_promote_plan(cx):
    out_path = cx.pile_path / "out"

    ops = []

    if not out_path.is_dir():
        return ops

    # validate top-level dirs
    for child in out_path.iterdir():
        if child.name not in ("collection", "filing"):
            fatal(f"invalid /out/ structure: {name}")

    # collect files

    col_dir = out_path / "collection"
    fil_dir = out_path / "filing"
    col_files = sorted(iter_files(col_dir)) if col_dir.is_dir() else []
    fil_files = sorted(iter_files(fil_dir)) if fil_dir.is_dir() else []
    if not col_files and not fil_files:
        fatal("/out/ directory empty")

    # validate files

    def validate_file(cx, src: Path, rel: Path):
        r = cx.resolve(rel)
        require_dataset(r.dataset)
        if r.path.is_file():
            if not files_equal(src, r.path):
                fatal(f"destination conflict for {rel}")


    for f in col_files:
        rel = Path("collection") / f.relative_to(col_dir)
        validate_file(cx, f, rel)
        r = cx.resolve(rel)
        action = "noop" if r.path.is_file() else "copy"
        ops.append(
            PromoteOp(
                src=f,
                dst=rel,
                dataset=r.dataset,
                action=action,
            )
        )

    for f in fil_files:
        rel = f.relative_to(fil_dir)
        if len(rel.parts) < 2:
            fatal("invalid filing structure")
        subset = rel.parts[0]
        subpath = Path(*rel.parts[1:])
        full_rel = Path("filing") / subset / subpath
        validate_file(cx, f, full_rel)
        r = cx.resolve(full_rel)
        action = "noop" if r.path.is_file() else "copy"
        ops.append(
            PromoteOp(
                src=f,
                dst=full_rel,
                dataset=r.dataset,
                action=action,
            )
        )

    return ops


def execute_promote_plan(cx, ops):
    datasets = {cx.pile_dataset}

    for op in ops:
        datasets.add(op.dataset)

    with writable_datasets(datasets):
        for op in ops:
            resolved = cx.resolve(op.dst)
            if op.action == "copy":
                cx.copy(op.src, resolved.path)
            safe_unlink(op.src)
