from dataclasses import dataclass
from pathlib import Path

from . import paths


@dataclass(frozen=True)
class StoragePolicy:
    pile_path: Path
    static_path: Path

    pile_dataset: str
    static_dataset: str

    def resolve(self, logical: paths.LogicalPath):
        if not isinstance(logical, paths.LogicalPath):
            raise ValueError("expected LogicalPath")

        if logical.domain == paths.StorageDomain.PILE:
            return paths.ResolvedPath(
                logical=logical,
                physical=self.pile_path / logical.relpath,
                dataset=self.pile_dataset,
            )

        if logical.domain == paths.StorageDomain.COLLECTION:
            return paths.ResolvedPath(
                logical=logical,
                physical=self.static_path / "collection" / logical.relpath,
                dataset=f"{self.static_dataset}/collection",
            )

        if logical.domain == paths.StorageDomain.FILING:
            subset = logical.relpath.parts[0] if logical.relpath.parts else ""
            return paths.ResolvedPath(
                logical=logical,
                physical=self.static_path / "filing" / logical.relpath,
                dataset=f"{self.static_dataset}/filing/{subset}",
            )

        raise ValueError(f"unsupported domain: {logical.domain}")
