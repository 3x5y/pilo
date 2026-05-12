#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import execution
from pilo import manifest_codec
from pilo import manifest_mutation
from pilo.front import rewrite


def print_preview(lines):
    for line in lines:
        print(line)


def main():
    cx = context.Context()

    script = rewrite.load_rewrite_script(cx)
    if not script.lines:
        error.fatal("missing command")

    ops = script.parse_ops()
    plan = rewrite.build_rewrite_plan(cx, ops)

    if rewrite.is_preview_mode(cx):
        preview = rewrite.preview_rewrite_plan(cx, plan)
        print_preview(preview)
        return

    manifest_path = cx.admin_path / "manifest/pile.manifest"
    entries = manifest_codec.load_manifest_entries(manifest_path)
    exec_plan = rewrite.rewrite_execution_plan(cx, plan, entries)
    execution.execute_plan(cx, exec_plan)


if __name__ == "__main__":
    error.run_main(main)
