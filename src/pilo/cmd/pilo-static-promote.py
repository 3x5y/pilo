#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import execution
from pilo import manifest_codec
from pilo.front import promote


def main():
    cx = context.Context()
    plan = promote.build_promote_plan(cx)
    if not plan:
        return

    manifest_path = cx.admin_path / "manifest/pile.manifest"
    entries = manifest_codec.load_manifest_entries(manifest_path)
    exec_plan = (
        promote.promote_execution_plan(
            cx,
            plan,
            entries,
        )
    )
    execution.execute_plan(cx, exec_plan)


if __name__ == "__main__":
    error.run_main(main)
