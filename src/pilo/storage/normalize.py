from dataclasses import dataclass

from .. import checks
from .. import fs
from .. import state
from .. import zfs


@dataclass(frozen=True)
class DatasetContract:
    name: str
    dataset_suffix: str
    filesystem: bool
    readonly: bool | None = None
    mount_attr: str | None = None


class dataset_contracts:

    ALL = [
        DatasetContract(
            name="active",
            dataset_suffix="active",
            filesystem=False,
        ),

        DatasetContract(
            name="admin",
            dataset_suffix="active/admin",
            filesystem=True,
            readonly=False,
            mount_attr="admin_path",
        ),

        DatasetContract(
            name="pile-intake",
            dataset_suffix="active/pile-intake",
            filesystem=True,
            readonly=False,
            mount_attr="intake_path",
        ),

        DatasetContract(
            name="pile-readonly",
            dataset_suffix="active/pile-readonly",
            filesystem=True,
            readonly=True,
            mount_attr="pile_path",
        ),

        DatasetContract(
            name="static",
            dataset_suffix="static",
            filesystem=False,
        ),

        DatasetContract(
            name="collection",
            dataset_suffix="static/collection",
            filesystem=True,
            readonly=True,
            mount_attr="collection_path",
        ),

        DatasetContract(
            name="filing",
            dataset_suffix="static/filing",
            filesystem=False,
            mount_attr="filing_path",
        ),
    ]

    # unused
    @staticmethod
    def lookup(name):
        for c in dataset_contracts.ALL:
            if c.name == name:
                return c
        return None


def contract_dataset(cx, contract):
    return f"{cx.root_dataset}/{contract.dataset_suffix}"


def contract_mountpoint(cx, contract):
    if contract.mount_attr is None:
        return None

    return getattr(cx, contract.mount_attr)


def apply_dataset_contracts(cx):

    for contract in dataset_contracts.ALL:
        dataset = contract_dataset(cx, contract)
        mountpoint = contract_mountpoint(cx, contract)

        if contract.filesystem:
            apply_filesystem(
                dataset,
                readonly=contract.readonly,
                mountpoint=mountpoint,
            )
        else:
            apply_namespace(
                dataset,
                mountpoint=mountpoint,
            )


def apply_namespace(dataset, mountpoint=None):
    checks.require_dataset(dataset)
    if mountpoint:
        zfs.set_mountpoint(dataset, mountpoint)
    zfs.set_canmount(dataset, False)


def apply_filesystem(dataset, mountpoint, readonly):
    checks.require_dataset(dataset)
    zfs.set_readonly(dataset, readonly)
    zfs.set_mountpoint(dataset, mountpoint)
    zfs.set_canmount(dataset, True)


def apply_ownership(cx):
    fs.ensure_owned(cx, cx.admin_path)
    fs.ensure_owned(cx, cx.intake_path)
    with zfs.dataset_writable(cx.pile_dataset):
        fs.ensure_owned(cx, cx.pile_path)
    with zfs.dataset_writable(cx.collection_dataset):
        fs.ensure_owned(cx, cx.collection_path)


def ensure_runtime_dirs(cx):
    pile = cx.pile_path
    with zfs.dataset_writable(cx.pile_dataset):
        fs.ensure_dir_owned(cx, pile / "in")
        fs.ensure_dir_owned(cx, pile / "sort")
        fs.ensure_dir_owned(cx, pile / "out")
        fs.ensure_dir_owned(cx, pile / "out" / "collection")
        fs.ensure_dir_owned(cx, pile / "out" / "filing")


def normalize_system(cx):
    apply_dataset_contracts(cx)
    zfs.mount()
    ensure_runtime_dirs(cx)
    apply_ownership(cx)


def validate_dataset_contract(cx, contract):
    issues = []
    dataset = contract_dataset(cx, contract)
    if not zfs.dataset_exists(dataset):
        issues.append(
            state.ValidationIssue(
                code="missing.required.dataset",
                message=f"missing dataset {dataset}",
                severity=state.ValidationSeverity.ERROR,
                component="datasets",
            )
        )
        return issues
    if contract.filesystem:
        readonly = zfs.get_readonly(dataset)
        if contract.readonly is not None:
            if readonly != contract.readonly:
                issues.append(
                    state.ValidationIssue(
                        code="invalid.readonly",
                        message=(
                            f"{dataset} readonly="
                            f"{readonly} expected={contract.readonly}"
                        ),
                        severity=state.ValidationSeverity.ERROR,
                        component="datasets",
                    )
                )
    return issues


def validate_dataset_contracts(cx):
    issues = []
    for contract in dataset_contracts.ALL:
        issues.extend(validate_dataset_contract(cx, contract))
    return issues
