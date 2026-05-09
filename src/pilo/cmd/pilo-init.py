#!/usr/bin/env python3

from pilo import context, error, validation
from pilo.back import normalize


def main():
    cx = context.Context()

    datasets = [
        cx.admin_dataset,
        cx.intake_dataset,
        cx.pile_dataset,
        cx.collection_dataset,
    ]
    for ds in datasets:
        validation.require_dataset(ds)

    normalize.normalize_system(cx)


if __name__ == "__main__":
    error.run_main(main)
