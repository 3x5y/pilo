#!/usr/bin/env python3

import sys

from pilo import error
from pilo.storage import replay


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: pilo stream-replay-all <path> [target_dataset]",
              file=sys.stderr)
        sys.exit(1)

    stream_dir = args[0]
    target_dataset = args[1] if len(args) > 1 else None

    paths = replay.find_streams(stream_dir)

    if not paths:
        return

    batch = replay.build_batch_replay_plan(paths, target_dataset)

    for r in replay.execute_batch_replay_plan(batch):
        print(f"{r.status} {r.stream} {r.target_dataset}")


if __name__ == "__main__":
    error.run_main(main)
