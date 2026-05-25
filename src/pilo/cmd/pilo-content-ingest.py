#!/usr/bin/env python3

from pilo.content import capture
from pilo.content import ingest
from pilo import checks
from pilo import context
from pilo import error
from pilo.content import execution
from pilo import fs


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
    exec_plan = ingest.build_exec_plan(cx, plan)
    execution.execute_plan(cx, exec_plan)


if __name__ == "__main__":
    error.run_main(main)
