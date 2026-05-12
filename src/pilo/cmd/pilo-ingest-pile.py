#!/usr/bin/env python3

from pilo import checks
from pilo import context
from pilo import error
from pilo import fs
from pilo import manifest_mutation
from pilo.front import capture
from pilo.front import ingest


def main():
    cx = context.Context()
    checks.require_dataset(cx.intake_dataset)
    checks.require_dataset(cx.pile_dataset)

    session = capture.capture_session(cx.intake_path)

    if not session.verify_if_present():
        error.fatal(
            f"capture verification failed: "
            f"{session.root}"
        )

    files = list(
        ingest.ingestible_capture_files(
            fs.iter_files(cx.intake_path)
        )
    )

    plan = ingest.build_ingest_plan(cx, files)
    ingest.execute_ingest_plan(cx, plan)

    manifest_path = cx.admin_path / "manifest/pile.manifest"
    muts = ingest.ingest_manifest_mutations(plan.ops, cx.pile_path)
    manifest_mutation.execute_manifest_mutations(cx, "pile", manifest_path, muts)


if __name__ == "__main__":
    error.run_main(main)
