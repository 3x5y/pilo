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


class PiloException(Exception):
    pass


class PiloError(PiloException):
    pass


class FatalError(PiloError):
    pass


def fatal(msg):
    raise FatalError(msg)


def run_main(f):
    try:
        f()
    except FatalError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def run(cmd, check=True):
    return subprocess.run(cmd, check=check)


def require_dataset(dataset):
    if not zfs.dataset_exists(dataset):
        fatal(f"missing required dataset: {dataset}")


def require_new_dataset(dataset):
    if zfs.dataset_exists(dataset):
        fatal(f"destination exists: {dataset}")


def require_child_dataset(dataset, root):
    if not dataset.startswith(root):
        fatal(f"dataset outside root: {dataset}")


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


def require_file(path):
    if not path.is_file():
        fatal(f"file does not exist: {path}")


def require_no_conflict(src, dst):
    if dst.is_file() and not files_equal(src, dst):
        fatal(f"destination conflict: {dst}")


def require_relative_path(path: Path):
    if path.is_absolute():
        fatal("absolute paths not allowed")
    if ".." in path.parts:
        fatal("parent traversal not allowed")


def require_same_domain(src, dst):
    src_domain = domain(src)
    dst_domain = domain(dst)

    if src_domain != dst_domain:
        fatal("cross-domain move not allowed")


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


def safe_rmdir(path: Path):
    path.rmdir()


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

    require_relative_path(path)

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


def find_incremental_base(src, dst):
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
        require_child_dataset(dataset, root)
        return dataset[len(root):].lstrip("/")

    def map(self, dataset: str) -> str:
        suffix = self._suffix(dataset, self.src_root)
        return f"{self.dst_root}/{suffix}" if suffix else self.dst_root

    def inverse(self, dataset: str) -> str:
        suffix = self._suffix(dataset, self.dst_root)
        return f"{self.src_root}/{suffix}" if suffix else self.src_root

    def validate_within_src(self, dataset: str):
        require_child_dataset(dataset, self.src_root)

    def validate_within_dst(self, dataset: str):
        require_child_dataset(dataset, self.dst_root)


@dataclass(frozen=True)
class RecoveryPlan:
    target: str
    replica: str
    snapshot: str
    recursive: bool


def build_recovery_plan(cx, target):
    mapping = DatasetMapping(cx.root_dataset, cx.replica_dataset)

    mapping.validate_within_src(target)
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
    require_dataset(src)
    if not last_dst:
        return ReplicationPlan( src, dst, last_src, None, "full")

    base = find_incremental_base(src, dst)

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


@dataclass(frozen=True)
class StatusMessage:
    level: str
    message: str


@dataclass
class SystemStatus:
    messages: list[StatusMessage] = None
    code: int = 0

    def __post_init__(self):
        if self.messages is None:
            self.messages = []

    def warn(self, msg):
        sm = StatusMessage(level="WARN", message=msg)
        self.messages.append(sm)
        self.code = 1

    def ok(self, msg):
        sm = StatusMessage(level="OK", message=msg)
        self.messages.append(sm)


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
    require_relative_path(path)


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

        op = RewriteOp( kind=kind, src=src_p, dst=dst_p)
        ops.append(op)

    return ops


@dataclass(frozen=True)
class ResolvedRewriteOp:
    op: RewriteOp
    src: Resolved
    dst: Resolved


def resolve_rewrite_op(cx, op: RewriteOp):
    src = cx.resolve(op.src)
    dst = cx.resolve(op.dst)
    return ResolvedRewriteOp(src=src, dst=dst, op=op)


def validate_rewrite_op(cx, op: ResolvedRewriteOp):
    require_same_domain(op.op.src, op.op.dst)
    require_file(op.src.path)
    require_no_conflict(op.src.path, op.dst.path)


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
    resolved = [resolve_rewrite_op(cx, op) for op in ops]
    validate_rewrite_ops(cx, resolved)
    return RewritePlan(ops=resolved)


def execute_rewrite_plan(cx, plan):
    muts = rewrite_plan_mutations(plan)
    execute_semantic_mutations(cx, muts)


def rewrite_plan_mutations(plan):
    mutations = []

    for op in plan.ops:
        dst_exists = op.dst.path.exists()

        if dst_exists:
            # currently unimplemented; throw error
            1/0
            mutations.append(
                SemanticMutation(
                    action="unlink",
                    src=op.src.path,
                    dst=None,
                    dataset=op.src.dataset,
                )
            )
        else:
            mutations.append(
                SemanticMutation(
                    action="move",
                    src=op.src.path,
                    dst=op.dst.path,
                    dataset=op.src.dataset,
                )
            )
    return mutations


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
    def build(name):
        manifest = cx.admin_path / "manifest" / f"{name}.manifest"
        root = manifest_subset_root(cx, name)
        return ManifestSubset(name=name, root=root, manifest=manifest)

    resolved = [build(name) for name in subsets]
    return ManifestUpdatePlan(subsets=resolved)


def execute_manifest_update_plan(cx, plan):
    for subset in plan.subsets:
        ensure_parent_dir(cx, subset.manifest)
        write_manifest(cx, subset.root, subset.manifest)
        msg = f"{subset.name} manifest update"
        commit_manifest_if_changed(cx, subset.manifest, msg)


def write_manifest(cx, root: Path, manifest: Path):
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        for line in generate_manifest_lines(root):
            tmp.write(line + "\n")

    ensure_parent_dir(cx, manifest)
    shutil.move(tmp_path, manifest)
    cx.ensure_owned(manifest)
    manifest.chmod(0o644)


def commit_manifest_if_changed(cx, manifest, message):
    repo = cx.admin_path / "manifest"
    cx.ensure_git_repo(repo)
    cx.git_commit_if_changed(repo, manifest, message)


@dataclass(frozen=True)
class IngestOp:
    src: Path
    dst: Path
    dataset: str
    action: str


def build_ingest_ops(cx, files):
    ops = []
    for src in files:
        rel = src.relative_to(cx.intake_path)
        dst = cx.pile_path / "in" / rel
        require_no_conflict(src, dst)
        if dst.exists():
            action = 'noop'
        else:
            action = 'move'
        ops.append(IngestOp(
            src=src,
            dst=dst,
            dataset=cx.pile_dataset,
            action=action
        ))
    return ops


def execute_ingest_ops(cx, ops):
    muts = ingest_plan_mutations(ops)
    execute_semantic_mutations(cx, muts)


def ingest_plan_mutations(ops):
    muts = []
    for op in ops:
        if op.action == "move":
            muts.append(
                SemanticMutation(
                    action="move",
                    src=op.src,
                    dst=op.dst,
                    dataset=op.dataset,
                )
            )
        elif op.action == "noop":
            muts.append(
                SemanticMutation(
                    action="unlink",
                    src=op.src,
                    dst=None,
                    dataset=op.dataset,
                )
            )
    return muts


@dataclass(frozen=True)
class PromoteOp:
    action: str
    src: Path
    dst: Path | None
    dataset: str


@dataclass(frozen=True)
class PromotePlan:
    ops: list[PromoteOp]


def build_promote_plan(cx):
    out_path = cx.pile_path / "out"

    ops = []

    if not out_path.is_dir():
        return None

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
        require_no_conflict(src, r.path)

    for f in col_files:
        rel = Path("collection") / f.relative_to(col_dir)
        validate_file(cx, f, rel)
        r = cx.resolve(rel)
        if not r.path.is_file():
            op = PromoteOp(action="copy",
                           src=f,
                           dst=r.path,
                           dataset=r.dataset)
            ops.append(op)
        op = PromoteOp(action="unlink",
                       src=f,
                       dst=None,
                       dataset=cx.pile_dataset)
        ops.append(op)

    for f in fil_files:
        rel = f.relative_to(fil_dir)
        if len(rel.parts) < 2:
            fatal("invalid filing structure")
        subset = rel.parts[0]
        subpath = Path(*rel.parts[1:])
        full_rel = Path("filing") / subset / subpath
        validate_file(cx, f, full_rel)
        r = cx.resolve(full_rel)
        if not r.path.is_file():
            op = PromoteOp(action="copy",
                           src=f,
                           dst=r.path,
                           dataset=r.dataset)
            ops.append(op)
        op = PromoteOp(action="unlink",
                       src=f,
                       dst=None,
                       dataset=cx.pile_dataset)
        ops.append(op)

    return RewritePlan(ops=ops)


def execute_promote_plan(cx, plan):
    muts = promote_plan_mutations(plan.ops)
    execute_semantic_mutations(cx, muts)


def promote_plan_mutations(ops):
    def build(op):
        return SemanticMutation(action=op.action,
                                src=op.src,
                                dst=op.dst,
                                dataset=op.dataset)
    return [build(op) for op in ops]


@dataclass(frozen=True)
class ReplaceOp:
    src: Path
    dst: Resolved


@dataclass(frozen=True)
class ReplacePlan:
    ops: list[ReplaceOp]


def build_replace_plan(cx, src, dst_rel):
    require_file(src)
    resolved = cx.resolve(dst_rel)
    require_file(resolved.path)
    require_dataset(resolved.dataset)
    op = ReplaceOp(src=src, dst=resolved)
    return ReplacePlan(ops=[op])


def execute_replace_plan(cx, plan):
    muts = replace_plan_mutations(plan)
    execute_semantic_mutations(cx, muts)


def replace_plan_mutations(plan):
    def build(op):
        return SemanticMutation(action="copy",
                                src=op.src,
                                dst=op.dst.path,
                                dataset=op.dst.dataset)
    return [build(op) for op in plan.ops]


@dataclass(frozen=True)
class SemanticMutation:
    action: str
    src: Path | None
    dst: Path | None
    dataset: str


def apply_semantic_mutation(cx, mut: SemanticMutation):
    if mut.action == "move":
        safe_move(cx, mut.src, mut.dst)
        return
    if mut.action == "copy":
        safe_copy(cx, mut.src, mut.dst)
        return
    if mut.action == "unlink":
        safe_unlink(mut.src)
        return
    if mut.action == "rmdir":
        safe_rmdir(mut.src)
        return
    fatal(f"unsupported mutation action: {mut.action}")


def execute_semantic_mutations(cx, mutations):
    datasets = {m.dataset for m in mutations}
    with writable_datasets(datasets):
        for mut in mutations:
            apply_semantic_mutation(cx, mut)


def mutation_manifest_domains(mutations):
    domains = set()
    for mut in mutations:
        ds = mut.dataset
        if ds.endswith("/pile"):
            domains.add("pile")
        elif "/static/collection" in ds:
            domains.add("collection")
        elif "/static/filing" in ds:
            domains.add("filing")
    return domains


def build_manifest_plan_for_mutations(cx, mutations):
    domains = sorted(mutation_manifest_domains(mutations))
    return build_manifest_update_plan(cx, domains)


@dataclass(frozen=True)
class PruneOp:
    path: Path
    dataset: str


@dataclass(frozen=True)
class PrunePlan:
    ops: list[PruneOp]


def build_prune_plan(root, dataset):
    keep = (
        root / "in",
        root / "out",
        root / "sort",
    )

    ops = []
    would_remove = set()

    def would_be_empty(path):
        for x in path.iterdir():
            if x not in would_remove:
                return False
        return True

    for path in sorted(root.rglob("*"), reverse=True):
        if path in keep:
            continue

        if path.is_dir() and would_be_empty(path):
            would_remove.add(path)
            op = PruneOp(path=path, dataset=dataset)
            ops.append(op)

    return PrunePlan(ops=ops)


def prune_mutations(plan):
    def build(op):
        return SemanticMutation(action="rmdir",
                                src=op.path,
                                dst=None,
                                dataset=op.dataset)
    return [build(op) for op in plan.ops]


def execute_prune_plan(cx, ops):
    mut = prune_mutations(ops)
    execute_semantic_mutations(cx, mut)


@dataclass(frozen=True)
class ManifestVerifyOp:
    subset: str
    root: Path
    manifest: Path


def manifest_subset_root(cx, subset):
    if subset == "pile":
        return cx.pile_path
    if subset in ("collection", "filing"):
        return cx.static_path / subset
    fatal(f"unsupported subset: {subset}")


def build_manifest_verify_plan(cx, subsets):
    def build(subset):
        manifest = cx.admin_path / "manifest" / f"{subset}.manifest"
        return ManifestVerifyOp(subset=subset,
                                root=manifest_subset_root(cx, subset),
                                manifest=manifest)
    return [build(subset) for subset in subsets]


def verify_manifest_op(op):
    m = op.manifest
    if not m.is_file() or m.stat().st_size == 0:
        return
    cmd = ["sha256sum", "--quiet", "--strict", "-c", m]
    try:
        subprocess.run(cmd, cwd=op.root, check=True)
    except subprocess.CalledProcessError:
        fatal(f"manifest verification failed: {op.subset}")


def execute_manifest_verify_plan(ops):
    for op in ops:
        verify_manifest_op(op)
