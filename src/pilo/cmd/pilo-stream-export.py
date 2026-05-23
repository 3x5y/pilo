#!/usr/bin/env python3

import sys

from pilo import error
from pilo.back.snapshot import parse_snapshot_name
from pilo.back.streams import export_incremental_stream


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: pilo stream-export <dataset@snapshot> [<dataset@base>]",
              file=sys.stderr)
        sys.exit(1)

    snap_arg = args[0]
    if "@" not in snap_arg:
        error.fatal(f"invalid snapshot reference: {snap_arg}")

    dataset, snap_name = snap_arg.split("@", 1)
    parsed = parse_snapshot_name(snap_name)
    if parsed is None:
        error.fatal(f"non-canonical snapshot name: {snap_name}")

    base_parsed = None
    if len(args) > 1:
        base_arg = args[1]
        if "@" not in base_arg:
            error.fatal(f"invalid snapshot reference: {base_arg}")
        _, base_name = base_arg.split("@", 1)
        base_parsed = parse_snapshot_name(base_name)
        if base_parsed is None:
            error.fatal(f"non-canonical snapshot name: {base_name}")

    filepath = export_incremental_stream(dataset, parsed, base=base_parsed)
    print(filepath)


if __name__ == "__main__":
    error.run_main(main)
