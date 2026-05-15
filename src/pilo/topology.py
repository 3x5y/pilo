from dataclasses import dataclass

from . import zfs


@dataclass(frozen=True)
class StorageTopology:
    primary_root: str
    secondary_roots: list[str]

    @property
    def attached_secondary_roots(self):
        return [ds for ds in self.secondary_roots if zfs.dataset_exists(ds)]

    def current_secondary_root(self):
        attached = self.attached_secondary_roots

        if not attached:
            return None

        if len(attached) > 1:
            raise RuntimeError(
                f"multiple secondary roots attached: {attached}"
            )

        return attached[0]
