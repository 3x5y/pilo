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

from .context import *
from .error import *
from .fs import *
from .manifest import *
from .mutation import *
from .paths import *
from .status import *
from .util import *
from .validation import *

from .back.normalize import *
from .back.recover import *
from .back.replication import *
from .back.restore import *
from .back.snapshot import *

from .front.ingest import *
from .front.manifest_verify import *
from .front.promote import *
from .front.prune import *
from .front.replace import *
from .front.rewrite import *


#####################
#    init stuff     #
#####################


#####################
# static file stuff #
#####################


#####################
# replication stuff #
#####################


#####################
#   restore stuff   #
#####################


def restore_from_snapshot(src, dst, snap, recursive):
    src_snap = f"{src}@{snap}"
    restore_dataset(src_snap, dst, recursive=recursive)



def validate_relative_path(path: Path):
    require_relative_path(path)