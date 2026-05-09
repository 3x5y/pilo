#!/usr/bin/env python3

import sys

from pilo import context, error, zfs


class Doctor:
    def __init__(self, cx: context.Context):
        self.cx = cx
        self.status = 0

    def warn(self, msg):
        print(f"ERROR: {msg}", file=sys.stderr)
        self.status = 1

    def check_dataset(self, dataset):
        if not zfs.dataset_exists(dataset):
            self.warn(f"missing required dataset: {dataset}")

    def check_readonly(self, dataset):
        try:
            if not zfs.get_readonly(dataset):
                self.warn(f"dataset not readonly: {dataset}")
        except Exception:
            self.warn(f"failed to read readonly state: {dataset}")

    def check_dir(self, path):
        if not path.is_dir():
            self.warn(f"missing directory: {path}")

    def run(self):
        cx = self.cx

        # dataset checks
        self.check_dataset(cx.intake_dataset)
        self.check_dataset(cx.pile_dataset)
        self.check_dataset(cx.collection_dataset)
        self.check_dataset(cx.admin_dataset)

        # readonly checks
        self.check_readonly(cx.pile_dataset)
        self.check_readonly(cx.collection_dataset)

        # directory checks
        self.check_dir(cx.pile_path / "in")
        self.check_dir(cx.pile_path / "out")
        self.check_dir(cx.pile_path / "sort")

        return self.status


def main():
    cx = context.Context()
    doctor = Doctor(cx)
    sys.exit(doctor.run())


if __name__ == "__main__":
    error.run_main(main)
