from contextlib import contextmanager, redirect_stderr, redirect_stdout
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


def make_context():
    return context.Context(environ={
        "PILO_ROOT": "tank/a",
        "PILO_REPLICA_ROOT": "backup/a",
        "PILO_ADMIN_DATASET": "tank/a/admin",
        "PILO_INTAKE_DATASET": "tank/a/intake",
        "PILO_PILE_DATASET": "tank/a/pile",
        "PILO_STATIC_DATASET": "tank/a/static",
        "PILO_PATH": "/tmp",
        "PILO_ADMIN_PATH": "/tmp/admin",
        "PILO_INTAKE_PATH": "/tmp/intake",
        "PILO_PILE_PATH": "/tmp/pile",
        "PILO_STATIC_PATH": "/tmp/static",
        "PILO_USER": "root",
    })


@contextmanager
def make_tmp_context():
    with tempfile.TemporaryDirectory() as td:
        yield context.Context(environ={
            "PILO_ROOT": "tank/a",
            "PILO_REPLICA_ROOT": "backup/a",
            "PILO_ADMIN_DATASET": "tank/a/admin",
            "PILO_INTAKE_DATASET": "tank/a/intake",
            "PILO_PILE_DATASET": "tank/a/pile",
            "PILO_STATIC_DATASET": "tank/a/static",
            "PILO_PATH": td,
            "PILO_ADMIN_PATH": f"{td}/admin",
            "PILO_INTAKE_PATH": f"{td}/intake",
            "PILO_PILE_PATH": f"{td}/pile",
            "PILO_STATIC_PATH": f"{td}/static",
            "PILO_USER": "root",
        })


@contextmanager
def tmpdir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@contextmanager
def healthy_snapshot_state(snapshot="tank/a/pile@r1", ts=1000, now=1001):
    snap_time = (snapshot, ts)
    p1 = patch("pilo.zfs.latest_snapshot_with_time", return_value=snap_time)
    p2 = patch("pilo.util.now_epoch", return_value=now)
    with (p1, p2):
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
