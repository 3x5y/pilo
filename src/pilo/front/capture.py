from dataclasses import dataclass
from pathlib import Path

from .. import manifest


CAPTURE_MANIFEST = "capture.manifest"


@dataclass(frozen=True)
class CaptureSession:
    root: Path
    manifest: Path

    def generate_manifest_lines(self):
        return list(manifest.generate_manifest_lines(self.root))

    def write_manifest(self, cx):
        manifest.write_manifest(cx, self.root, self.manifest)

    def verify(self):
        if not self.manifest.exists():
            return False
        lines = self.manifest.read_text().splitlines()
        return manifest.verify_manifest_lines(self.root, lines)


def capture_manifest_path(root):
    return root / CAPTURE_MANIFEST


def capture_session(root):
    manifest=capture_manifest_path(root)
    return CaptureSession(root=root, manifest=manifest)
