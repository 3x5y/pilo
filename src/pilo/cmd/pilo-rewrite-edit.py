#!/usr/bin/env python3

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from pilo import context
from pilo import error
from pilo import fs


def has_output_script(cx):
    return (
        len(cx.args) >= 1
        and cx.args[0] == "--output-script"
    )


def output_script_path(cx):
    if len(cx.args) < 2:
        error.fatal("--output-script requires path")
    return cx.args[1]


def has_apply(cx):
    return "--apply" in cx.args


def generate_script(before, after):
    if len(after) != len(set(after)):
        error.fatal("duplicate entries in edited list")
    for old, new in zip(before, after):
        if old != new:
            yield f"mv\t{old}\t{new}"


def parse_edited_lines(lines):
    return [
        line.strip()
        for line in lines
        if line.strip()
    ]


def build_script_lines(before, after):

    if len(after) != len(set(after)):
        error.fatal("duplicate entries in edited list")

    for old, new in zip(before, after):
        if old != new:
            yield f"mv\t{old}\t{new}"


def list_files(cx):
    return sorted(
        str(p.relative_to(cx.pile_path))
        for p in fs.iter_files(cx.pile_path / "in")
    )


def print_files(cx):
    for line in list_files(cx):
        print(line)


def print_script(cx, edited_lines):
    before = list_files(cx)
    after = parse_edited_lines(edited_lines)
    for line in generate_script(before, after):
        print(line)


def write_edit_buffer(lines):
    with tempfile.NamedTemporaryFile( "w+", delete=False) as f:
        tmp = Path(f.name)
        for line in lines:
            f.write(line + "\n")
    return tmp


def edit_file(path):
    editor = os.environ.get("EDITOR", "vi")
    cmd = editor.split()
    args = [str(path)]
    subprocess.run(cmd + args, check=True)
    return path.read_text().splitlines()


def build_script(before, after):
    return "\n".join(build_script_lines(before, after))


def write_script_file(path, script):
    with open(path, "w") as f:
        f.write(script)


def execute_script(script):
    cmd = "pilo rewrite".split()
    args = [script]
    return subprocess.run(cmd + args)


def interactive(cx):
    before = list_files(cx)
    tmp = write_edit_buffer(before)
    try:
        edited = edit_file(tmp)
        after = parse_edited_lines(edited)
        script = build_script(before, after)
        if has_output_script(cx):
            path = output_script_path(cx)
            write_script_file(path, script)
            if not has_apply(cx):
                return

        result = execute_script(script)
        sys.exit(result.returncode)

    finally:
        tmp.unlink(missing_ok=True)


def main():
    cx = context.Context()

    if len(cx.args) >= 1 and cx.args[0] == "--dump":
        print_files(cx)
        return

    if len(cx.args) >= 1 and cx.args[0] == "--script":
        inlines = sys.stdin.read().splitlines()
        print_script(cx, inlines)
        return

    interactive(cx)


if __name__ == "__main__":
    error.run_main(main)
