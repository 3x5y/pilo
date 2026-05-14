from contextlib import nullcontext

from . import error
from . import fs
from . import zfs

from .mutation_types import (
    MoveMutation,
    CopyMutation,
    UnlinkMutation,
    RmdirMutation,
)


class MutationExecutor:

    requires_write_access = False

    def __init__(self, cx):
        self.cx = cx

    def apply(self, mut):
        raise NotImplementedError


class LiveExecutor(MutationExecutor):

    requires_write_access = True

    def apply(self, mut):
        apply_mutation(self.cx, mut)


def execute_move(cx, mut):
    fs.safe_move(cx, mut.src, mut.dst)


def execute_copy(cx, mut):
    fs.safe_copy(cx, mut.src, mut.dst)


def execute_unlink(cx, mut):
    fs.safe_unlink(mut.path)


def execute_rmdir(cx, mut):
    fs.safe_rmdir(mut.path)


EXEC_HANDLERS = {
    MoveMutation: execute_move,
    CopyMutation: execute_copy,
    UnlinkMutation: execute_unlink,
    RmdirMutation: execute_rmdir,
}


def apply_mutation(cx, mut):

    try:
        handler = EXEC_HANDLERS[type(mut)]
    except KeyError:
        error.fatal(
            f"unsupported mutation type: "
            f"{type(mut).__name__}"
        )

    handler(cx, mut)


def apply_mutations(executor, mutations):

    if executor.requires_write_access:
        datasets = {m.dataset for m in mutations}
        context = zfs.writable_datasets(datasets)
    else:
        context = nullcontext()

    with context:
        for mut in mutations:
            executor.apply(mut)


def execute_fs_mutations(cx, mutations):
    executor = LiveExecutor(cx)
    apply_mutations(executor, mutations)
