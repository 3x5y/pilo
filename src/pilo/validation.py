from pathlib import Path

from . import checks
from . import policy


require_dataset = checks.require_dataset
require_new_dataset = checks.require_new_dataset
require_snapshot = checks.require_snapshot
require_snapshot_of_dataset =  checks.require_snapshot_of_dataset
require_within_dataset = checks.require_within_dataset
require_file = checks.require_file
require_no_conflict = checks.require_no_conflict

require_child_dataset = policy.require_child_dataset
require_relative_path = policy.require_relative_path
require_same_domain = policy.require_same_domain


class validate:
    @staticmethod
    def dataset_exists(ds):
        checks.require_dataset(ds)

    @staticmethod
    def snapshot_exists(snap):
        checks.require_snapshot(snap)

    @staticmethod
    def new_dataset(ds):
        checks.require_new_dataset(ds)
