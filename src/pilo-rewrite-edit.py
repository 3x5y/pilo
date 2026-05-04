#!/usr/bin/env python3

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pilo


def generate_script(before, after):
    if len(after) != len(set(after)):
        pilo.fatal("duplicate entries in edited list")
    for old, new in zip(before, after):
        if old != new:
            yield f"mv\t{old}\t{new}"


def list_files(cx):
    return sorted(
        str(p.relative_to(cx.pile_path))
        for p in pilo.iter_files(cx.pile_path / "in")
    )


def print_files(cx):
    for line in list_files(cx):
        print(line)


def print_script(cx, edited_lines):
    before = list_files(cx)
    after = [line.strip() for line in edited_lines if line.strip()]
    for line in generate_script(before, after):
        print(line)


def interactive(cx):
    before = list_files(cx)

    with tempfile.NamedTemporaryFile("w+", delete=False) as f:
        tmp = Path(f.name)
        for line in before:
            f.write(line + "\n")

    editor = os.environ.get("EDITOR", "vi")
    cmd = editor.split() + [str(tmp)]
    subprocess.run(cmd, check=True)
    after = tmp.read_text().splitlines()
    script = "\n".join(generate_script(before, after))
    result = subprocess.run(["pilo", "rewrite", script])
    tmp.unlink(missing_ok=True)
    sys.exit(result.returncode)


def main():
    cx = pilo.Context()

    if len(cx.args) >= 1 and cx.args[0] == "--dump":
        print_files(cx)
        return

    if len(cx.args) >= 1 and cx.args[0] == "--script":
        inlines = sys.stdin.read().splitlines()
        print_script(cx, inlines)
        return

    interactive(cx)


if __name__ == "__main__":
    main()
