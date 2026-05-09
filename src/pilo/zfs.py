import subprocess

from . import error


def simple_pipe(src_cmd, sink_cmd):
    source = subprocess.Popen(src_cmd, stdout=subprocess.PIPE)
    sink = subprocess.Popen(sink_cmd, stdin=source.stdout)
    source.stdout.close()
    sink.communicate()
    if source.wait() != 0 or sink.returncode != 0:
        error.fatal("replication failed")


def dataset_exists(dataset):
    result = subprocess.run(
        ["zfs", "list", dataset],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def get_prop(dataset, propname):
    cmd = 'zfs get -Ho value'.split()
    args = [propname, dataset]
    result = subprocess.run(cmd + args,
                            capture_output=True,
                            text=True,
                            check=True)
    return result.stdout.strip()


def set_prop(dataset, propval, recursive=False):
    if recursive:
        for child in list_filesystems(dataset):
            set_prop(child, propval, recursive=False)
    else:
        cmd = ["zfs", "set", propval, dataset]
        subprocess.run(cmd, check=True)


def get_readonly(dataset):
    return get_prop(dataset, 'readonly') == 'on'


def set_readonly(dataset, state):
    prop = 'on' if state else 'off'
    set_prop(dataset, f'readonly={prop}')


def list_filesystems(root):
    result = subprocess.run(
        ["zfs", "list", "-r", "-t", "filesystem", "-Ho", "name", root],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def list_snapshots(dataset):
    cmd = 'zfs list -t snapshot -Ho name -s creation ' + dataset
    result = subprocess.run(
        cmd.split(),
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.strip().splitlines() if line]


def latest_snapshot(dataset):
    try:
        snaps = list_snapshots(dataset)
    except subprocess.CalledProcessError:
        return None
    else:
        return snaps and snaps[-1] or None


def list_guids(dataset):
    result = subprocess.run(
        ["zfs", "list", "-t", "snapshot", "-Ho", "guid", dataset],
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(result.stdout.splitlines())


def snapshot_guids(dataset):
    result = subprocess.run(
        ["zfs", "list", "-t", "snapshot", "-o", "name,guid", dataset],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().splitlines()
    return [line.split() for line in lines if line]


def get_latest_guid(dataset):
    result = subprocess.run(
        ["zfs", "list", "-t", "snapshot", "-Ho", "guid", "-s", "creation", dataset],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = result.stdout.strip().splitlines()
    return lines[-1] if lines else None


def snapshot(name: str, dataset: str):
    if not dataset:
        error.fatal("dataset required for snapshot")
    cmd = ["zfs", "snapshot", "-r", f"{dataset}@{name}"]
    subprocess.run(cmd, check=True)


def hold(tag, snapshot):
    cmd = ["zfs", "hold", "-r", tag, snapshot]
    subprocess.run(cmd, check=True)


def latest_snapshot_with_time(dataset):
    cmd = ["zfs", "list", "-p", "-t", "snapshot", "-o", "name,creation", "-s", "creation", dataset]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    lines = [l for l in result.stdout.splitlines() if l.startswith(dataset + "@")]

    if not lines:
        return None, None

    name, ts = lines[-1].split()

    try:
        return name, int(ts)
    except Exception:
        return name, None


def destroy(dataset, recursive=True):
    cmd = ["zfs", "destroy"]
    if recursive:
        cmd.append("-r")
    cmd.append(dataset)
    subprocess.run(cmd, check=False)


def snapshot_exists(snap):
    return subprocess.run(
        ["zfs", "list", "-t", "snapshot", snap],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def create_parent(dataset):
    parent = dataset.rsplit("/", 1)[0]
    if parent and not dataset_exists(parent):
        subprocess.run(["zfs", "create", "-p", parent], check=False)


def replicate_full(snapshot, dst):
    send = ["zfs", "send", "-h", "-R", snapshot]
    recv = ["zfs", "receive", "-u",
            "-o", "readonly=on",
            "-o", "mountpoint=none",
            dst]
    simple_pipe(send, recv)
    set_prop(dst, "canmount=off", recursive=True)


def replicate_incremental(base, snapshot, dst):
    send = ["zfs", "send", "-h", "-R", "-I", base, snapshot]
    recv = ["zfs", "receive", "-u",
            "-o", "readonly=on",
            "-o", "mountpoint=none",
            dst]
    simple_pipe(send, recv)
    set_prop(dst, "canmount=off", recursive=True)


def send_recv(src_snap, dst, recursive=False):
    send_cmd = ["zfs", "send"]
    if recursive:
        send_cmd.append("-R")
    send_cmd.append(src_snap)
    recv_cmd = ["zfs", "receive", dst]
    simple_pipe(send_cmd, recv_cmd)


def mount():
    subprocess.run(["zfs", "mount", "-a"], check=True)