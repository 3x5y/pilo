#!/bin/sh
set -e

DATA_ROOT="$TEST_ROOT"
REPL_ROOT="$TEST_REPLICA"

# --- create canonical datasets ---
zfs create -p "$DATA_ROOT/active/pile"
zfs create -p "$DATA_ROOT/active/projects"
zfs create -p "$DATA_ROOT/archive"

echo "pile-data" > /tank/data/active/pile/file.txt
echo "project-data" > /tank/data/active/projects/code.txt
echo "archive-data" > /tank/data/archive/doc.txt

# snapshot everything consistently
zfs snapshot -r "$DATA_ROOT@baseline"

# replicate all datasets
zfs send -R "$DATA_ROOT@baseline" | zfs receive -F "$REPL_ROOT"

# --- simulate total loss ---
zfs destroy -r "$DATA_ROOT"

# --- recovery (dataset-by-dataset, explicit) ---
system-recover-baseline "$REPL_ROOT/active/pile" \
                        "$DATA_ROOT/active/pile" baseline >/dev/null
system-recover-baseline "$REPL_ROOT/active/projects" \
                        "$DATA_ROOT/active/projects" baseline >/dev/null
system-recover-baseline "$REPL_ROOT/archive" \
                        "$DATA_ROOT/archive" baseline >/dev/null

# --- verify ---
grep -q "pile-data" "/tank/data/active/pile/.zfs/snapshot/baseline/file.txt"
grep -q "project-data" "/tank/data/active/projects/.zfs/snapshot/baseline/code.txt"
grep -q "archive-data" "/tank/data/archive/.zfs/snapshot/baseline/doc.txt"
