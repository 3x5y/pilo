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

    pilo.apply_dataset_contract(cx)
    pilo.ensure_runtime_dirs(cx)
    pilo.apply_ownership(cx)


if __name__ == "__main__":
    main()
