#!/usr/bin/env python3

import os
import subprocess
import sys

import pilo


def run_verify(src, dst):
    result = subprocess.run(
        ["pilo", "replication-verify", src, dst],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def extract_status(output):
    for line in output.splitlines():
        if line.startswith("STATUS="):
            return line.split("=", 1)[1]
    return None


def main():
    src = os.environ["PILO_ROOT"]
    dst = os.environ["PILO_REPLICA_ROOT"]

    verify_status, output = run_verify(src, dst)
    status = extract_status(output)

    if status == "OK":
        return

    elif status in ("EMPTY", "BEHIND"):
        subprocess.run(["pilo", "replicate", src, dst], check=True)

    elif status == "DIVERGED":
        print(output, end="")
        sys.exit(verify_status)

    else:
        print(output, end="")
        pilo.fatal("unknown verification state")

    # --- post verification ---
    post_status_code, post_output = run_verify(src, dst)
    post_state = extract_status(post_output)

    if post_state != "OK":
        print(post_output, end="")
        pilo.fatal("replication did not converge")

    sys.exit(0)


if __name__ == "__main__":
    main()
