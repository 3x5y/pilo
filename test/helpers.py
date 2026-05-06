
import importlib
from pathlib import Path
import pilo


def import_command(name):
    modname = f'pilo-{name}'
    filename = modname + '.py'
    modpath = Path(pilo.__file__).parent / filename
    spec = importlib.util.spec_from_file_location(modname, modpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_context():
    return pilo.Context(environ={
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
