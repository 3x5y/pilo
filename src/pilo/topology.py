from dataclasses import dataclass

from . import zfs


@dataclass(frozen=True)
class SecondaryState:
    root: str
    configured: bool
    carrier_attached: bool
    dataset_exists: bool
    initialized: bool
    current: bool


def carrier_root(dataset):
    parts = dataset.split("/")
    if len(parts) <= 1:
        return dataset
    return "/".join(parts[:-1])


@dataclass(frozen=True)
class StorageTopology:
    primary_root: str
    secondary_roots: list[str]

    def secondary_states(self):
        states = []
        attached = []
        existing = []
        for root in self.secondary_roots:
            carrier = carrier_root(root)
            carrier_attached = zfs.dataset_exists(carrier)
            dataset_exists = zfs.dataset_exists(root)
            initialized = False
            if dataset_exists:
                initialized = bool(zfs.latest_snapshot(root))
            state = SecondaryState(
                root=root,
                configured=True,
                carrier_attached=carrier_attached,
                dataset_exists=dataset_exists,
                initialized=initialized,
                current=False,
            )
            #if carrier_attached:
            #    attached.append(state)
            if dataset_exists:
                existing.append(state)
            states.append(state)

        #if len(attached) > 1:
        if len(existing) > 1:
            raise RuntimeError(
                f"multiple secondary roots attached: "
                #f"{[s.root for s in attached]}"
                f"{[s.root for s in existing]}"
            )

        #current_root = attached[0].root if attached else None
        current_root = existing[0].root if existing else None
        return [
            SecondaryState(
                root=s.root,
                configured=s.configured,
                carrier_attached=s.carrier_attached,
                dataset_exists=s.dataset_exists,
                initialized=s.initialized,
                current=(s.root == current_root),
            )
            for s in states
        ]

    @property
    def attached_secondary_roots(self):
        return [
            s.root for s in self.secondary_states()
            #if s.carrier_attached
            if s.dataset_exists
        ]

    def current_secondary_state(self):
        for state in self.secondary_states():
            if state.current:
                return state
        return None

    def current_secondary_root(self):
        current = self.current_secondary_state()
        if current:
            return current.root
        return None
