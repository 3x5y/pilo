from contextlib import contextmanager, ExitStack
from dataclasses import dataclass
import subprocess

from . import error


PILO_ROLE_PROPERTY = "pilo:role"

ROLE_PRIMARY = "primary"
ROLE_REPLICA = "replica"


@dataclass(frozen=True)
class PoolEntry:
    name: str
    health: str


@dataclass(frozen=True)
class DatasetEntry:
    name: str
    readonly: str
    mountpoint: str
    canmount: str


@dataclass(frozen=True)
class SnapshotEntry:
    name: str
    creation: int


def run(cmd, *, check=True, capture_output=False, text=True, **kw):
    return subprocess.run(cmd,
                          check=check,
                          capture_output=capture_output,
                          text=text,
                          **kw)


def run_get_status(cmd, **kw):
    result = run(cmd,
                 stdout=subprocess.DEVNULL,
                 stderr=subprocess.DEVNULL,
                 check=False,
                 **kw)
    return result.returncode


def run_get_output(cmd, **kw):
    result = run(cmd, capture_output=True, **kw)
    return result.stdout


def run_get_lines(cmd, **kw):
    return run_get_output(cmd, **kw).strip().splitlines()


def simple_pipe(src_cmd, sink_cmd):
    source = subprocess.Popen(src_cmd, stdout=subprocess.PIPE)
    sink = subprocess.Popen(sink_cmd, stdin=source.stdout)
    source.stdout.close()
    sink.communicate()
    if source.wait() != 0 or sink.returncode != 0:
        error.fatal("replication failed")


def zfs_list(fields, *args, types=None, sort=None, parsable=True, check=True):
    cmd = "zfs list -H".split()
    if parsable:
        cmd.append("-p")
    if types is not None:
        cmd += ["-t", types]
    if sort is not None:
        cmd += ["-s", sort]
    cmd += ["-o", ",".join(fields)]
    cmd += list(args)
    return run_get_lines(cmd, check=check)


def list_pools():
    cmd = ["zpool", "list", "-H", "-o", "name,health"]
    lines = run_get_lines(cmd, check=False)
    entries = []
    for line in lines:
        if not line:
            continue
        name, health = line.split("\t")
        entry = PoolEntry(name=name, health=health)
        entries.append(entry)
    return entries


def list_datasets(root=None):

    args = ["-r"]

    if root is not None:
        args.append(root)

    fields = [
        "name",
        "readonly",
        "mountpoint",
        "canmount",
    ]
    lines = zfs_list(fields, *args, types="filesystem", check=False)
    entries = []
    for line in lines:
        if not line:
            continue
        name, readonly, mountpoint, canmount = line.split("\t")
        entry = DatasetEntry(
            name=name,
            readonly=readonly,
            mountpoint=mountpoint,
            canmount=canmount,
        )
        entries.append(entry)
    return entries


def list_snapshot_entries(dataset):

    lines = zfs_list(
        [
            "name",
            "creation",
        ],
        dataset,
        types="snapshot",
        sort="creation",
        check=False,
    )

    entries = []

    for line in lines:
        if not line:
            continue
        name, creation = line.split("\t")
        try:
            ts = int(creation)
        except ValueError:
            ts = 0
        entries.append(
            SnapshotEntry(
                name=name,
                creation=ts,
            )
        )

    return entries


def dataset_exists(dataset):
    cmd = "zfs list".split()
    args = [dataset]
    status =  run_get_status(cmd + args)
    return status == 0


def snapshot_exists(snap):
    cmd = "zfs list -t snapshot".split()
    args = [snap]
    status =  run_get_status(cmd + args)
    return status == 0


def has_prop(dataset, propname):
    cmd = "zfs get -H -o value".split()
    args = [propname, dataset]
    result = run(cmd + args, check=False, capture_output=True)
    return result.returncode == 0


def get_prop(dataset, propname):
    cmd = 'zfs get -Ho value'.split()
    args = [propname, dataset]
    out = run_get_output(cmd + args)
    return out.strip()


def set_prop(dataset, propval, recursive=False):
    if recursive:
        for child in list_filesystems(dataset):
            set_prop(child, propval, recursive=False)
    else:
        cmd = "zfs set".split()
        args = [propval, dataset]
        run(cmd + args)


def get_readonly(dataset):
    state = get_prop(dataset, 'readonly')
    return state == 'on'


def set_readonly(dataset, setting):
    state = 'on' if setting else 'off'
    set_prop(dataset, f'readonly={state}')


def get_mountpoint(dataset):
    return get_prop(dataset, 'mountpoint')


def set_mountpoint(dataset, mountpoint):
    mp = get_mountpoint(dataset)
    if mountpoint and mp != str(mountpoint):
        set_prop(dataset, f"mountpoint={mountpoint}")


def get_canmount(dataset):
    return get_prop(dataset, 'canmount') == 'on'


def set_canmount(dataset, value):
    if get_canmount(dataset) != value:
        setting = value and 'on' or 'off'
        set_prop(dataset, f'canmount={setting}')


def get_role(dataset):
    value = get_prop(dataset, PILO_ROLE_PROPERTY)
    if value == "-":
        return None
    return value


def set_role(dataset, role):
    if role not in (ROLE_PRIMARY, ROLE_REPLICA):
        error.fatal(f"invalid role: {role}")
    set_prop(dataset, f"{PILO_ROLE_PROPERTY}={role}")


def is_primary_root(dataset):
    return get_role(dataset) == ROLE_PRIMARY


def is_replica_root(dataset):
    return get_role(dataset) == ROLE_REPLICA


def list_role_roots():
    roots = []
    for pool in list_pools():
        datasets = list_datasets(pool.name)
        for ds in datasets:
            role = get_role(ds.name)
            if role is None:
                continue
            roots.append((ds.name, role))
    return roots


def list_filesystems(root):
    cmd = "zfs list -r -t filesystem -Ho name".split()
    args = [root]
    return run_get_lines(cmd + args)


def list_snapshots(dataset):
    cmd = "zfs list -t snapshot -Ho name -s creation".split()
    args = [dataset]
    return run_get_lines(cmd + args, check=False)


def latest_snapshot(dataset):
    snaps = list_snapshots(dataset)
    return snaps and snaps[-1] or None


def list_guids(dataset):
    cmd = "zfs list -t snapshot -Ho guid".split()
    args = [dataset]
    return sorted(run_get_lines(cmd + args, check=False))


def snapshot_guids(dataset):
    cmd = "zfs list -t snapshot -o name,guid".split()
    args = [dataset]
    lines = run_get_lines(cmd + args)
    return [line.split() for line in lines if line]


def get_latest_guid(dataset):
    cmd = "zfs list -t snapshot -Ho guid -s creation".split()
    args = [dataset]
    lines = run_get_lines(cmd + args, check=False)
    return lines[-1] if lines else None


def latest_snapshot_with_time(dataset):
    cmd = "zfs list -p -t snapshot -o name,creation -s creation".split()
    args = [dataset]
    lines = run_get_lines(cmd + args, check=False)
    matches = [l for l in lines if l.startswith(dataset + "@")]

    if not matches:
        return None, None

    name, ts = matches[-1].split()

    try:
        return name, int(ts)
    except Exception:
        return name, None


def snapshot(name: str, dataset: str):
    if not dataset:
        error.fatal("dataset required for snapshot")
    cmd = "zfs snapshot -r".split()
    snap = f"{dataset}@{name}"
    args = [snap]
    run(cmd + args)


def hold(tag, snapshot):
    cmd = "zfs hold -r".split()
    args = [tag, snapshot]
    run(cmd + args)


def release(tag, snapshot):
    cmd = "zfs release -r".split()
    args = [tag, snapshot]
    run(cmd + args)


def list_holds(snapshot):
    cmd = "zfs holds -Hp".split()
    args = [snapshot]
    lines = run_get_lines(cmd + args, check=False)
    holds = []
    for line in lines:
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            holds.append((parts[0], parts[1]))
    return holds


def held_snapshots(dataset, tag=None):
    snaps = list_snapshots(dataset)
    result = []
    for snap in snaps:
        holds = list_holds(snap)
        if not holds:
            continue
        if tag is None:
            result.append(snap)
        elif any(t == tag for _, t in holds):
            result.append(snap)
    return result


def create_parent(dataset):
    parent = dataset.rsplit("/", 1)[0]
    if parent and not dataset_exists(parent):
        cmd = "zfs create -p".split()
        args = [parent]
        run(cmd + args, check=False)


def replicate_full(snapshot, dst):
    send = "zfs send -h -R".split()
    send_args = [snapshot]
    recv = "zfs receive -u -o readonly=on -o mountpoint=none".split()
    recv_args = [dst]
    simple_pipe(send + send_args, recv + recv_args)
    set_prop(dst, "canmount=off", recursive=True)


def replicate_incremental(base, snapshot, dst):
    send = "zfs send -h -R -I".split()
    send_args = [base, snapshot]
    recv = "zfs receive -u -o readonly=on -o mountpoint=none".split()
    recv_args = [dst]
    simple_pipe(send + send_args, recv + recv_args)
    set_prop(dst, "canmount=off", recursive=True)


def send_recv(src_snap, dst, recursive=False):
    send_cmd = "zfs send".split()
    if recursive:
        send_cmd.append("-R")
    send_args = [src_snap]
    recv_cmd = "zfs recv".split()
    recv_args = [dst]
    simple_pipe(send_cmd + send_args, recv_cmd + recv_args)


def mount():
    cmd = "zfs mount -a".split()
    run(cmd)


def create_dataset(dataset):
    cmd = "zfs create -o canmount=off -o mountpoint=none ".split()
    args = [dataset]
    run(cmd + args)


@contextmanager
def dataset_writable(dataset):
    was = get_readonly(dataset)
    if was:
        set_readonly(dataset, False)
    try:
        yield
    finally:
        if was:
            set_readonly(dataset, True)


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
