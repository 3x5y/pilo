from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

from . import error
from . import fs
from . import manifest_policy
from . import manifest_update
from . import zfs

from .mutation_events import OperationEvent
from .mutation_types import (
    CopyMutation,
    MoveMutation,
    RmdirMutation,
    UnlinkMutation,
    SemanticMutation,
)

from .mutation_exec import (
    MutationExecutor,
    LiveExecutor,
    apply_mutation,
    apply_mutations,
    execute_fs_mutations,
)

from .mutation_preview import (
    PreviewExecutor,
    get_preview_events,
    render_mutation_preview,
    event_for_mutation,
)

from .mutation_render import (
    render_event,
    render_events,
    render_mutation,
    render_mutations,
)
