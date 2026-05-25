#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.content import promote
from pilo.front import execution
from pilo.front import manifest


def main():
    cx = context.Context()
    plan = promote.build_promote_plan(cx)
    if not plan:
        return

    manifest_path = cx.admin_path / "manifest/pile.manifest"
    entries = manifest.load_manifest_entries(manifest_path)
    exec_plan = promote.build_exec_plan(cx, plan, entries)
    execution.execute_plan(cx, exec_plan)


if __name__ == "__main__":
    error.run_main(main)
