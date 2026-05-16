from dataclasses import dataclass

from . import zfs


@dataclass(frozen=True)
class SecondaryState:
    root: str
    configured: bool
    attached: bool
    initialized: bool
    current: bool


@dataclass(frozen=True)
class StorageTopology:
    primary_root: str
    secondary_roots: list[str]

    def secondary_states(self):

        attached = []

        for root in self.secondary_roots:
            is_attached = zfs.dataset_exists(root)

            state = SecondaryState(
                root=root,
                configured=True,
                attached=is_attached,
                initialized=is_attached,
                current=False,
            )

            if is_attached:
                attached.append(state)

        if len(attached) > 1:
            raise RuntimeError(
                f"multiple secondary roots attached: "
                f"{[s.root for s in attached]}"
            )

        current_root = attached[0].root if attached else None
        states = []
        for root in self.secondary_roots:
            is_attached = zfs.dataset_exists(root)
            states.append(
                SecondaryState(
                    root=root,
                    configured=True,
                    attached=is_attached,
                    initialized=is_attached,
                    current=(root == current_root),
                )
            )
        return states

    @property
    def attached_secondary_roots(self):
        return [s.root for s in self.secondary_states()
                if s.attached]

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
