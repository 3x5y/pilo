from dataclasses import dataclass
from pathlib import Path

from ..front import manifest


CAPTURE_MANIFEST = ".manifest"


@dataclass(frozen=True)
class CaptureSession:
    root: Path
    manifest: Path

    def manifest_excludes(self):
        return [Path(CAPTURE_MANIFEST)]

    def generate_manifest_lines(self):
        exclude = self.manifest_excludes()
        return list(manifest.generate_manifest_lines(self.root, exclude))

    def write_manifest(self, cx):
        lines = self.generate_manifest_lines()
        out = "\n".join(lines) + "\n" if lines else ""
        self.manifest.write_text(out)

    def verify(self):
        if not self.manifest.exists():
            return False

        lines = self.manifest.read_text().splitlines()

        return manifest.verify_manifest_lines(
            self.root,
            lines,
            exclude=self.manifest_excludes(),
        )

    def verify_if_present(self):
        if not self.manifest.exists():
            return True
        return self.verify()


def capture_manifest_path(root):
    return root / CAPTURE_MANIFEST


def capture_session(root):
    manifest=capture_manifest_path(root)
    return CaptureSession(root=root, manifest=manifest)
