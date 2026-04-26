#!/bin/sh
set -e

# --- create full system state ---
echo pile > /tmp/p.txt
system-capture /tmp/p.txt
system-ingest-pile

echo admin > /tank/data/active/admin/code.txt

with_dataset_writable tank/data/static \
    sh -c "echo static > /tank/data/static/doc.txt"

system-snapshot baseline
system-replicate

# --- destroy everything ---
zfs destroy -r $TEST_ROOT

# --- recover ONLY pile ---
system-recover-baseline \
    $TEST_REPLICA/active/pile-readonly \
    $TEST_ROOT/active/pile-readonly baseline >/dev/null

# --- system should now be inconsistent ---
capture_status system-status
assert_command_fail "partial recovery not detected"
echo "$OUTPUT" | assert_grep "incomplete"
