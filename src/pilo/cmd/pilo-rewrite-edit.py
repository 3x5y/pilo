#!/usr/bin/env python3

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pilo import context
from pilo import error
from pilo import fs
from pilo.front import rewrite


@dataclass(frozen=True)
class EditEntry:
    ident: int
    path: str


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

    before_entries = [EditEntry(idx, path)
                      for idx, path in enumerate(before, start=1)]
    after_entries = parse_edit_lines(after)
    seen_paths = set()

    for entry in after_entries:
        if entry.path in seen_paths:
            error.fatal("duplicate entries in edited list")
        seen_paths.add(entry.path)

    before_by_id = {entry.ident: entry for entry in before_entries}

    for edited in after_entries:
        original = before_by_id.get(edited.ident)
        if original is None:
            error.fatal(
                f"unknown edit identifier: "
                f"{edited.ident}"
            )
        if original.path != edited.path:
            yield f"mv\t{original.path}\t{edited.path}"


def list_files(cx):
    return sorted(
        str(p.relative_to(cx.pile_path))
        for p in fs.iter_files(cx.pile_path / "in")
    )


def render_edit_lines(paths):
    for idx, path in enumerate(paths, start=1):
        yield f"{idx}\t{path}"


def parse_edit_lines(lines):

    entries = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)

        if len(parts) != 2:
            error.fatal(f"invalid edit line: {line}")

        ident_str, path = parts

        try:
            ident = int(ident_str)
        except ValueError:
            error.fatal(
                f"invalid edit identifier: "
                f"{ident_str}"
            )
        entry = EditEntry(ident=ident, path=path.strip())
        entries.append(entry)

    return entries


def print_files(cx):
    for line in render_edit_lines(list_files(cx)):
        print(line)


def print_script(cx, edited_lines):
    before = list_files(cx)
    for line in generate_script(before, edited_lines):
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


def build_script(before, after_lines):
    lines = list(generate_script(before, after_lines))
    ops = []
    for op in lines:
        ops += rewrite.parse_rewrite_ops([op])
    script = rewrite.RewriteScript.from_ops(ops)
    return script.render_text()


def write_script_file(path, script):
    with open(path, "w") as f:
        f.write(script)


def execute_script(script):
    cmd = "pilo rewrite".split()
    args = [script]
    return subprocess.run(cmd + args)


def interactive(cx):
    before = list_files(cx)
    tmp = write_edit_buffer(render_edit_lines(before))
    try:
        edited = edit_file(tmp)
        script = build_script(before, edited)
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

    if cx.args and cx.args[0] == "--dump":
        print_files(cx)
    elif cx.args and cx.args[0] == "--script":
        inlines = sys.stdin.read().splitlines()
        print_script(cx, inlines)
    else:
        interactive(cx)


if __name__ == "__main__":
    error.run_main(main)
