#!/usr/bin/env python3

from pilo import checks
from pilo import context
from pilo import error
from pilo import fs
from pilo import manifest
from pilo.front import ingest


def main():
    cx = context.Context()
    checks.require_dataset(cx.intake_dataset)
    checks.require_dataset(cx.pile_dataset)

    files = list(fs.iter_files(cx.intake_path))
    plan = ingest.build_ingest_plan(cx, files)
    ingest.execute_ingest_plan(cx, plan)

    plan = manifest.build_manifest_update_plan(cx, ["pile"])
    manifest.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    error.run_main(main)
