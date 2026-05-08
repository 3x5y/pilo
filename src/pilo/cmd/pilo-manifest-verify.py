#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()
    domains = ["pile", "collection", "filing"]
    plan = pilo.build_manifest_verify_plan(cx, domains)
    pilo.execute_manifest_verify_plan(plan)


if __name__ == "__main__":
    pilo.run_main(main)
