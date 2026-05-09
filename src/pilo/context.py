from dataclasses import dataclass
from pathlib import Path
import os
import pwd
import sys

from . import error
from . import paths
from . import policy
#from .storage_policy import StoragePolicy


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


@dataclass(frozen=True)
class StoragePolicy:
    domain: paths.StorageDomain
    root_path: Path
    root_dataset: str

    @classmethod
    def for_domain(cls, cx, domain):

        if domain == paths.StorageDomain.PILE:
            return cls(
                domain=domain,
                root_path=cx.pile_path,
                root_dataset=cx.pile_dataset,
            )

        if domain == paths.StorageDomain.COLLECTION:
            return cls(
                domain=domain,
                root_path=cx.collection_path,
                root_dataset=cx.collection_dataset,
            )

        if domain == paths.StorageDomain.FILING:
            return cls(
                domain=domain,
                root_path=cx.filing_path,
                root_dataset=cx.filing_dataset,
            )

        raise AssertionError(f"domain not implemented: {domain}")

    def physical_path(self, relpath: Path):
        return self.root_path / relpath

    def dataset_for(self, relpath: Path):
        if self.domain == paths.StorageDomain.FILING:
            if not relpath.parts:
                raise AssertionError("missing filing subset")
            subset = relpath.parts[0]
            return f"{self.root_dataset}/{subset}"
        return self.root_dataset


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

        #self.storage_policy = StoragePolicy(
        #    pile_path=self.pile_path,
        #    static_path=self.static_path,
        #    pile_dataset=self.pile_dataset,
        #    static_dataset=self.static_dataset,
        #)

    def storage_policy(self, domain):
        return StoragePolicy.for_domain(self, domain)

    def resolve(self, rel: Path) -> paths.ResolvedPath:
        logical = paths.parse_logical_path(rel)
        policy = self.storage_policy(logical.domain)
        return paths.ResolvedPath(
            logical=logical,
            physical=policy.physical_path(
                logical.relpath,
            ),
            dataset=policy.dataset_for(
                logical.relpath,
            ),
        )
