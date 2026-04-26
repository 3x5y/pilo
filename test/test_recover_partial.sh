#!/bin/sh
set -e

DATA_ROOT=$TEST_ROOT
REPL_ROOT=$TEST_REPLICA

# --- create full system state ---

# pile
echo pile > /tmp/p.txt
system-capture /tmp/p.txt
system-ingest-pile

# admin
mkdir -p /tank/data/active/admin
echo admin > /tank/data/active/admin/code.txt

# archive
mkdir -p /tank/data/archive
echo archive > /tank/data/archive/doc.txt

# snapshot + replicate
zfs snapshot -r $DATA_ROOT@baseline
system-replicate $DATA_ROOT $REPL_ROOT

# --- destroy everything ---
zfs destroy -r $DATA_ROOT

# --- recover ONLY pile ---
system-recover-baseline \
    $REPL_ROOT/active/pile-readonly \
    $DATA_ROOT/active/pile-readonly baseline >/dev/null

# --- system should now be inconsistent ---

capture_status system-status

[ $STATUS -ne 0 ] || fail "partial recovery not detected"

echo "$OUTPUT" | assert_grep "incomplete"
