from contextlib import (
    ExitStack,
    contextmanager,
    redirect_stderr,
    redirect_stdout,
)
import importlib
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pilo import context
from pilo import error


@contextmanager
def assert_fatal(testcase):
    stderr = StringIO()
    with redirect_stderr(stderr):
        with testcase.assertRaises(error.FatalError) as cx:
            yield cx


# unused
@contextmanager
def suppress_stderr():
    stream = StringIO()
    with redirect_stderr(stream):
        yield stream


@contextmanager
def suppress_stdout():
    stream = StringIO()
    with redirect_stdout(stream):
        yield stream


def import_command(name):
    modname = f'pilo-{name}'
    filename = modname + '.py'
    modpath = Path(__file__).parent / '../src/pilo/cmd' / filename
    spec = importlib.util.spec_from_file_location(modname, modpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_environ(root, **kw):
    env = {
        "PILO_PRIMARY_ROOT": "tank/a",
        "PILO_SECONDARY_ROOTS": "backup/a",
        "PILO_ADMIN_DATASET": "tank/a/admin",
        "PILO_INTAKE_DATASET": "tank/a/intake",
        "PILO_PILE_DATASET": "tank/a/pile",
        "PILO_STATIC_DATASET": "tank/a/static",
        "PILO_PATH": root,
        "PILO_ADMIN_PATH": f"{root}/admin",
        "PILO_INTAKE_PATH": f"{root}/intake",
        "PILO_PILE_PATH": f"{root}/pile",
        "PILO_STATIC_PATH": f"{root}/static",
        "PILO_USER": "ubuntu",
    }
    env.update(kw)
    return env


def make_context(root='/tmp', **kw):
    env = make_environ(root, **kw)
    return context.Context(environ=env)


@contextmanager
def make_tmp_context(**kw):
    with tempfile.TemporaryDirectory() as td:
        yield make_context(td, **kw)


@contextmanager
def tmpdir(**kw):
    with tempfile.TemporaryDirectory(**kw) as td:
        yield Path(td)


@contextmanager
def tmpfile(mode="w+", prefix="pilo.tmp.", dir=None, **kw):
    if dir is None:
        dir = "/tmp"
    with tempfile.NamedTemporaryFile(mode=mode, prefix=prefix, dir=dir, **kw) as f:
        yield Path(f.name)


@contextmanager
def healthy_snapshot_state(snapshot="tank/a/pile@r1", ts=1000, now=1001):
    snap_time = (snapshot, ts)
    p1 = patch("pilo.zfs.latest_snapshot_with_time", return_value=snap_time)
    p2 = patch("pilo.util.now_epoch", return_value=now)
    with (p1, p2):
        yield


@contextmanager
def healthy_system_state():
    from pilo.back.replication import ReplicationStatus
    p1 = patch("pilo.state.collect_snapshot_validation",
               return_value=[])
    p2 = patch("pilo.back.replication.replication_status",
               return_value=(ReplicationStatus.OK, None))
    with ExitStack() as stack:
        stack.enter_context(p1)
        stack.enter_context(p2)
        yield


class TestCase(unittest.TestCase):

    def tearDown(self):
        check = 'admin intake pile static'.split()
        tmp = Path('/tmp')
        for x in check:
            d = tmp / x
            if d.exists():
                import os, shutil
                print()
                print("test didn't clean up")
                print(self)
                print(d)
                shutil.rmtree(d)
                os._exit(1)

    def assert_fatal(self):
        return assert_fatal(self)
