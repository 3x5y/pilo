from . import error

from .mutation_events import OperationEvent
from .mutation_types import (
    MoveMutation,
    CopyMutation,
    UnlinkMutation,
    RmdirMutation,
)


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
        error.fatal(
            f"unsupported mutation type: "
            f"{type(mut).__name__}"
        )
    return handler(mut)


def render_mutations(mutations):
    return [render_mutation(m) for m in mutations]


def render_event(ev):
    if ev.dst is None:
        return f"{ev.kind} {ev.src}"
    return f"{ev.kind} {ev.src} -> {ev.dst}"


def render_events(events):
    return [render_event(ev) for ev in events]
