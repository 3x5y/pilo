#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile

with_writable $PILE \
    mkdir -p /$PILE/out/filing/

# simulate weird path
with_writable $PILE \
    sh -c "mv /$PILE/in/file.txt /$PILE/out/filing//file.txt"

capture_status system-static-promote

assert_command_fail
