#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()
    pilo.require_dataset(cx.intake_dataset)
    pilo.require_dataset(cx.pile_dataset)

    files = list(pilo.iter_files(cx.intake_path))
    ops = pilo.build_ingest_ops(cx, files)
    pilo.execute_ingest_ops(cx, ops)

    plan = pilo.build_manifest_update_plan(cx, ["pile"])
    pilo.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    pilo.run_main(main)
