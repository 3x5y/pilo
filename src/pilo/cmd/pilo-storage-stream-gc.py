#!/usr/bin/env python3

import os
from pathlib import Path

from pilo import error
from pilo.storage import stream_gc
from pilo.storage.streams import stream_output_path


def main():
    dataset = os.environ["PILO_PRIMARY_ROOT"]
    output_path = stream_output_path()
    keep = int(os.environ.get("PILO_STREAM_GC_KEEP", "0"))
    gc_path = os.environ.get("PILO_STREAM_GC_PATH")
    if gc_path:
        gc_path = Path(gc_path)

    plan = stream_gc.build_gc_plan(dataset, output_path, keep=keep)
    for p in stream_gc.execute_gc_plan(plan, output_path, gc_path=gc_path):
        print(f"PRUNE {p}")


if __name__ == "__main__":
    error.run_main(main)
