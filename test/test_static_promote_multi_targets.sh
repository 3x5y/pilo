#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

zfs create -p -o readonly=on tank/data/static/filing/2024

echo a > /tmp/a.txt
echo b > /tmp/b.txt

system-capture /tmp/a.txt
system-capture /tmp/b.txt
system-ingest-pile

with_writable $PILE mkdir -p /$PILE/out/filing/2024
with_writable $PILE mkdir -p /$PILE/out/filing/2025

with_writable $PILE mv /$PILE/in/a.txt /$PILE/out/filing/2024/a.txt
with_writable $PILE mv /$PILE/in/b.txt /$PILE/out/filing/2025/b.txt

system-static-promote

assert_file_exists /tank/data/static/filing/2024/a.txt
assert_file_exists /tank/data/static/filing/2025/b.txt
