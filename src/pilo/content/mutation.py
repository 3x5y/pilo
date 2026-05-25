from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

from .. import error
from .. import fs
from .. import zfs


# --- types (was mutation_types.py) ---

@dataclass(frozen=True)
class MoveMutation:
    src: Path
    dst: Path
    dataset: str


@dataclass(frozen=True)
class CopyMutation:
    src: Path
    dst: Path
    dataset: str


@dataclass(frozen=True)
class UnlinkMutation:
    path: Path
    dataset: str


@dataclass(frozen=True)
class RmdirMutation:
    path: Path
    dataset: str


# --- events (was mutation_events.py) ---

@dataclass(frozen=True)
class OperationEvent:
    kind: str
    src: Path
    dst: Path | None
    dataset: str


# --- exec (was mutation_exec.py) ---

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
        error.fatal(f"unsupported mutation type: {type(mut).__name__}")
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


# --- preview (was mutation_preview.py) ---

class PreviewExecutor(MutationExecutor):

    requires_write_access = False

    def __init__(self, cx):
        super().__init__(cx)
        self.events = []

    def apply(self, mut):
        e = event_for_mutation(mut)
        self.events.append(e)


def event_for_move(mut):
    return OperationEvent(
        kind="move", src=mut.src, dst=mut.dst, dataset=mut.dataset,
    )


def event_for_copy(mut):
    return OperationEvent(
        kind="copy", src=mut.src, dst=mut.dst, dataset=mut.dataset,
    )


def event_for_unlink(mut):
    return OperationEvent(
        kind="unlink", src=mut.path, dst=None, dataset=mut.dataset,
    )


def event_for_rmdir(mut):
    return OperationEvent(
        kind="rmdir", src=mut.path, dst=None, dataset=mut.dataset,
    )


EVENT_HANDLERS = {
    MoveMutation: event_for_move,
    CopyMutation: event_for_copy,
    UnlinkMutation: event_for_unlink,
    RmdirMutation: event_for_rmdir,
}


def event_for_mutation(mut):
    try:
        handler = EVENT_HANDLERS[type(mut)]
    except KeyError:
        raise RuntimeError(f"unsupported mutation type: {type(mut).__name__}")
    return handler(mut)


def get_preview_events(cx, mutations):
    executor = PreviewExecutor(cx)
    apply_mutations(executor, mutations)
    return executor.events


def render_mutation_preview(cx, mutations):
    events = get_preview_events(cx, mutations)
    return render_events(events)


# --- render (was mutation_render.py) ---

def render_move(mut):
    return f"move {mut.src} -> {mut.dst}"


def render_copy(mut):
    return f"copy {mut.src} -> {mut.dst}"


def render_unlink(mut):
    return f"unlink {mut.path}"


def render_rmdir(mut):
    return f"rmdir {mut.path}"


RENDER_HANDLERS = {
    MoveMutation: render_move,
    CopyMutation: render_copy,
    UnlinkMutation: render_unlink,
    RmdirMutation: render_rmdir,
}


def render_mutation(mut):
    try:
        handler = RENDER_HANDLERS[type(mut)]
    except KeyError:
        error.fatal(f"unsupported mutation type: {type(mut).__name__}")
    return handler(mut)


def render_mutations(mutations):
    return [render_mutation(m) for m in mutations]


def render_event(ev):
    if ev.dst is None:
        return f"{ev.kind} {ev.src}"
    return f"{ev.kind} {ev.src} -> {ev.dst}"


def render_events(events):
    return [render_event(ev) for ev in events]
