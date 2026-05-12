#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import manifest_mutation
from pilo.front import promote


def main():
    cx = context.Context()
    plan = promote.build_promote_plan(cx)
    if not plan:
        return
    promote.execute_promote_plan(cx, plan)

    muts = promote.promote_manifest_mutations(
        plan.ops,
        cx.pile_path,
        cx.static_path / "collection",
        cx.static_path / "filing",
    )

    for subset in ("pile", "collection", "filing"):
        manifest_path = cx.admin_path / "manifest" / f"{subset}.manifest"
        manifest_mutation.execute_manifest_mutations(
            cx,
            subset,
            manifest_path,
            muts,
        )

if __name__ == "__main__":
    error.run_main(main)
