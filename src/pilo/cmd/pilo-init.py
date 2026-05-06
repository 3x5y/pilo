#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()

    datasets = [
        cx.admin_dataset,
        cx.intake_dataset,
        cx.pile_dataset,
        cx.collection_dataset,
    ]
    for ds in datasets:
        pilo.require_dataset(ds)

    pilo.normalize_system(cx)


if __name__ == "__main__":
    main()
