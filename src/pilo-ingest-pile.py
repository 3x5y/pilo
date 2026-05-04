#!/usr/bin/env python3

import shutil
from pathlib import Path

import pilo


def main():
    cx = pilo.Context()
    pilo.require_dataset(cx.intake_dataset)
    pilo.require_dataset(cx.pile_dataset)

    files = list(pilo.iter_files(cx.intake_path))

    def validate_files():
        for src in files:
            rel = src.relative_to(cx.intake_path)
            dst = cx.pile_path / "in" / rel

            if dst.is_file() and not pilo.files_equal(src, dst):
                pilo.fatal(f"name collision with different content: '{rel}'")

    def apply_changes():
        for src in files:
            rel = src.relative_to(cx.intake_path)
            dst = cx.pile_path / "in" / rel

            if dst.is_file():
                if pilo.files_equal(src, dst):
                    src.unlink()
                else:
                    raise Error('validation is broken')
            else:
                cx.move(src, dst)

    validate_files()

    with pilo.dataset_writable(cx.pile_dataset):
        apply_changes()

    pilo.run(["pilo", "manifest-update"])


if __name__ == "__main__":
    main()
