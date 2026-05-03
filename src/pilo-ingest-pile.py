#!/usr/bin/env python3

import os
import shutil

import pilo as P


def main():
    intake_dataset = P.require_env("PILO_INTAKE_DATASET")
    pile_dataset = P.require_env("PILO_PILE_DATASET")
    intake_path = P.require_env("PILO_INTAKE_PATH")
    pile_path = P.require_env("PILO_PILE_PATH")
    user = P.require_env("PILO_USER")
    P.require_dataset(intake_dataset)
    P.require_dataset(pile_dataset)

    files = P.list_files(intake_path)

    def validate_files():
        for src in files:
            rel = os.path.relpath(src, intake_path)
            dst = os.path.join(pile_path, "in", rel)

            if os.path.isfile(dst) and not P.files_equal(src, dst):
                P.fatal(f"name collision with different content: '{rel}'")

    def apply_changes():
        for src in files:
            rel = os.path.relpath(src, intake_path)
            dst = os.path.join(pile_path, "in", rel)
            dst_dir = os.path.dirname(dst)

            if os.path.isfile(dst):
                if P.files_equal(src, dst):
                    os.remove(src)
                else:
                    P.fatal(f"name collision with different content: '{rel}'")
            else:
                P.ensure_dir(dst_dir, user)
                shutil.move(src, dst)
                P.run(["chown", f"{user}:{user}", dst])

    validate_files()

    with P.dataset_writable(pile_dataset):
        apply_changes()

    P.run(["pilo", "manifest-update"])


if __name__ == "__main__":
    main()
