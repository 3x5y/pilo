#!/usr/bin/env python3

import os
import shutil

import pilo


def main():
    cx = pilo.Context(os.environ)
    pilo.require_dataset(cx.intake_dataset)
    pilo.require_dataset(cx.pile_dataset)

    files = pilo.list_files(cx.intake_path)

    def validate_files():
        for src in files:
            rel = os.path.relpath(src, cx.intake_path)
            dst = os.path.join(cx.pile_path, "in", rel)

            if os.path.isfile(dst) and not pilo.files_equal(src, dst):
                pilo.fatal(f"name collision with different content: '{rel}'")

    def apply_changes():
        for src in files:
            rel = os.path.relpath(src, cx.intake_path)
            dst = os.path.join(cx.pile_path, "in", rel)

            if os.path.isfile(dst):
                if pilo.files_equal(src, dst):
                    os.remove(src)
                else:
                    # redundant with validate check above?
                    pilo.fatal(f"name collision with different content: '{rel}'")
            else:
                cx.move(src, dst)

    validate_files()

    with pilo.dataset_writable(cx.pile_dataset):
        apply_changes()

    pilo.run(["pilo", "manifest-update"])


if __name__ == "__main__":
    main()
