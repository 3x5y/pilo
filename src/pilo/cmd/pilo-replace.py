#!/usr/bin/env python3

from pathlib import Path

from pilo import context
from pilo import error
from pilo import manifest_mutation
from pilo.front import replace


def main():
    cx = context.Context()

    if len(cx.args) < 2:
        error.fatal("missing arguments")

    src = Path(cx.args[0])
    dst_rel = Path(cx.args[1])

    plan = replace.build_replace_plan(cx, src, dst_rel)
    replace.execute_replace_plan(cx, plan)

    manifest_path = cx.admin_path / "manifest/pile.manifest"
    muts = replace.replace_manifest_mutations(plan, cx.pile_path)
    manifest_mutation.execute_manifest_mutations(
        cx,
        "pile",
        manifest_path,
        muts,
    )

if __name__ == "__main__":
    error.run_main(main)
