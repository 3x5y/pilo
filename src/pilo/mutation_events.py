from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OperationEvent:
    kind: str
    src: Path
    dst: Path | None
    dataset: str
