from dataclasses import dataclass
from pathlib import Path
import os
import pwd
import sys

from . import error
from . import paths
from . import policy
from .storage_policy import StoragePolicy


@dataclass(frozen=True)
class DatasetMapping:
    src_root: str
    dst_root: str

    def _suffix(self, dataset: str, root: str) -> str:
        policy.require_child_dataset(dataset, root)
        return dataset[len(root):].lstrip("/")

    def map(self, dataset: str) -> str:
        suffix = self._suffix(dataset, self.src_root)
        return f"{self.dst_root}/{suffix}" if suffix else self.dst_root

    def inverse(self, dataset: str) -> str:
        suffix = self._suffix(dataset, self.dst_root)
        return f"{self.src_root}/{suffix}" if suffix else self.src_root

    def validate_within_src(self, dataset: str):
        policy.require_child_dataset(dataset, self.src_root)

    def validate_within_dst(self, dataset: str):
        policy.require_child_dataset(dataset, self.dst_root)


class Context:
    def __init__(self, environ=os.environ, args=sys.argv):
        self.root_dataset = environ["PILO_ROOT"]
        self.replica_dataset = environ["PILO_REPLICA_ROOT"]
        self.admin_dataset = environ["PILO_ADMIN_DATASET"]
        self.intake_dataset = environ["PILO_INTAKE_DATASET"]
        self.pile_dataset = environ["PILO_PILE_DATASET"]
        self.static_dataset = environ["PILO_STATIC_DATASET"]
        #self.collection_dataset = f"{self.static_dataset}/collection"
        #self.filing_dataset = f"{self.static_dataset}/filing"

        self.path = Path(environ["PILO_PATH"])
        self.admin_path = Path(environ["PILO_ADMIN_PATH"])
        self.intake_path = Path(environ["PILO_INTAKE_PATH"])
        self.pile_path = Path(environ["PILO_PILE_PATH"])
        self.static_path = Path(environ["PILO_STATIC_PATH"])
        #self.collection_path = Path(environ["PILO_COLLECTION_PATH"])
        #self.filing_path = Path(environ["PILO_FILING_PATH"])
        #self.collection_path = self.static_path / 'collection'
        #self.filing_path = self.static_path / 'filing'

        self.user = environ["PILO_USER"]
        self.user_id = pwd.getpwnam(self.user).pw_uid
        self.args = args and args[1:] or []

        self.storage_policy = StoragePolicy(
            pile_path=self.pile_path,
            static_path=self.static_path,
            pile_dataset=self.pile_dataset,
            static_dataset=self.static_dataset,
        )

    def resolve(self, rel: Path) -> paths.ResolvedPath:
        logical = paths.parse_logical_path(rel)
        return self.storage_policy.resolve(logical)
