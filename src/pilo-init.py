#!/usr/bin/env python3

from pathlib import Path

import pilo


def main():
    cx = pilo.Context()

    pilo.require_dataset(cx.admin_dataset)
    pilo.require_dataset(cx.intake_dataset)
    pilo.require_dataset(cx.pile_dataset)
    pilo.require_dataset(cx.collection_dataset)

    pile = cx.pile_path

    cx.ensure_dir(pile / "in")
    cx.ensure_dir(pile / "sort")
    cx.ensure_dir(pile / "out")
    cx.ensure_dir(pile / "out" / "collection")
    cx.ensure_dir(pile / "out" / "filing")

    pilo.zfs_set_readonly(cx.pile_dataset, True)
    pilo.zfs_set_readonly(cx.collection_dataset, True)


if __name__ == "__main__":
    main()
