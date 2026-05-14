from .mutation_events import OperationEvent

from .mutation_exec import (
    MutationExecutor,
    apply_mutations,
)

from .mutation_render import render_events

from .mutation_types import (
    MoveMutation,
    CopyMutation,
    UnlinkMutation,
    RmdirMutation,
)


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
        kind="move",
        src=mut.src,
        dst=mut.dst,
        dataset=mut.dataset,
    )


def event_for_copy(mut):

    return OperationEvent(
        kind="copy",
        src=mut.src,
        dst=mut.dst,
        dataset=mut.dataset,
    )


def event_for_unlink(mut):

    return OperationEvent(
        kind="unlink",
        src=mut.path,
        dst=None,
        dataset=mut.dataset,
    )


def event_for_rmdir(mut):

    return OperationEvent(
        kind="rmdir",
        src=mut.path,
        dst=None,
        dataset=mut.dataset,
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
        raise RuntimeError(
            f"unsupported mutation type: "
            f"{type(mut).__name__}"
        )
    return handler(mut)


def get_preview_events(cx, mutations):
    executor = PreviewExecutor(cx)
    apply_mutations(executor, mutations)
    return executor.events


def render_mutation_preview(cx, mutations):
    events = get_preview_events(cx, mutations)
    return render_events(events)
