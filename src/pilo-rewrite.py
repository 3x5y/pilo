#!/usr/bin/env python3

import sys
from pathlib import Path
from dataclasses import dataclass

import pilo


@dataclass
class Op:
    kind: str
    src: Path
    dst: Path


def parse_ops(lines):
    ops = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split("\t")

        if len(parts) != 3:
            pilo.fatal(f"invalid command: {line}")

        kind, src, dst = parts

        if kind != "mv":
            pilo.fatal(f"unsupported operation: '{kind}'")

        src_p = Path(src)
        dst_p = Path(dst)

        if src_p.is_absolute() or ".." in src_p.parts:
            pilo.fatal("invalid source path")

        if dst_p.is_absolute() or ".." in dst_p.parts:
            pilo.fatal("invalid destination path")

        ops.append(Op(kind, src_p, dst_p))

    return ops


def validate_ops(cx, ops):
    seen_src = set()
    seen_dst = set()

    for op in ops:
        if op.src in seen_src:
            pilo.fatal(f"duplicate source in script: {op.src}")
        if op.dst in seen_dst:
            pilo.fatal(f"destination conflict in script: {op.dst}")

        seen_src.add(op.src)
        seen_dst.add(op.dst)

        src_domain = pilo.domain(op.src)
        dst_domain = pilo.domain(op.dst)

        if src_domain != dst_domain:
            pilo.fatal("cross-domain move not allowed")

        src_abs = cx.resolve_path(op.src)
        dst_abs = cx.resolve_path(op.dst)

        if not src_abs.is_file():
            pilo.fatal(f"source missing: {op.src}")

        if dst_abs.is_file() and not pilo.files_equal(src_abs, dst_abs):
            pilo.fatal(f"destination conflict: {op.dst}")


def apply_op(cx, op):
    src_abs = cx.resolve_path(op.src)
    dst_abs = cx.resolve_path(op.dst)
    dataset = cx.resolve_dataset(op.src)

    with pilo.dataset_writable(dataset):
        if dst_abs.exists():
            src_abs.unlink()
        else:
            cx.ensure_dir(dst_abs.parent)
            src_abs.rename(dst_abs)


def apply_ops(cx, ops):
    for op in ops:
        apply_op(cx, op)


def main():
    cx = pilo.Context()
    if len(cx.args) < 1:
        pilo.fatal("missing command")
    cmd = cx.args[0]
    ops = parse_ops(cmd.splitlines())
    validate_ops(cx, ops)
    apply_ops(cx, ops)
    pilo.run(["pilo", "manifest-update"])


if __name__ == "__main__":
    main()
