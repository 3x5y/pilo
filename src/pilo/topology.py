from dataclasses import dataclass

from . import error
from . import zfs


@dataclass(frozen=True)
class SecondaryConfig:
    label: str
    root: str


def parse_secondary_roots(envstr):
    tokens = envstr.split()
    configs = []
    for token in tokens:
        if not token:
            continue
        label = token.split("/")[0]
        configs.append(SecondaryConfig(label=label, root=token))

    labels = [c.label for c in configs]
    if len(labels) != len(set(labels)):
        error.fatal(f"duplicate secondary labels: {labels}")

    roots = [c.root for c in configs]
    if len(roots) != len(set(roots)):
        error.fatal(f"duplicate secondary roots: {roots}")

    return configs


@dataclass(frozen=True)
class SecondaryState:
    label: str
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
    secondary_configs: list[SecondaryConfig]

    def secondary_states(self):
        states = []
        attached = []
        for config in self.secondary_configs:
            carrier = carrier_root(config.root)
            carrier_attached = zfs.dataset_exists(carrier)
            dataset_exists = zfs.dataset_exists(config.root)
            initialized = False
            if dataset_exists:
                initialized = bool(zfs.latest_snapshot(config.root))
            state = SecondaryState(
                label=config.label,
                root=config.root,
                configured=True,
                carrier_attached=carrier_attached,
                dataset_exists=dataset_exists,
                initialized=initialized,
                current=False,
            )
            if carrier_attached:
                attached.append(state)
            states.append(state)

        if len(attached) > 1:
            raise RuntimeError(
                f"multiple secondary roots detected: "
                f"{[s.root for s in attached]}"
            )

        current_root = attached[0].root if attached else None
        return [
            SecondaryState(
                label=s.label,
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
            c.root for c in self.secondary_configs
            if zfs.dataset_exists(carrier_root(c.root))
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
