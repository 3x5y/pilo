#!/usr/bin/env python3

import sys

from pilo import error
from pilo.back import replay


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: pilo stream-replay <stream.zfs> [target_dataset]",
              file=sys.stderr)
        sys.exit(1)

    stream_path = args[0]
    target_dataset = args[1] if len(args) > 1 else None

    plan = replay.build_replay_plan(stream_path, target_dataset)
    result = replay.execute_replay_plan(plan)

    print(f"{result.status} {result.snapshot} {result.target_dataset}")


if __name__ == "__main__":
    error.run_main(main)
