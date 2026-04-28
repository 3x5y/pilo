#!/bin/sh
set -e

repl_pile=$TEST_REPLICA/active/pile-readonly
admin=$ACTIVE/admin
snap=baseline
echo admin-data > /$admin/admin.txt
mkfile pile-data p.txt
capture_file p.txt
system-ingest-pile
with_writable $STATIC \
    touch /$STATIC/doc.txt
system-snapshot $snap
system-replicate

# --- destroy everything ---
zfs destroy -r $TEST_ROOT

# --- recover ONLY pile ---
system-recover-baseline $repl_pile $PILE $snap >/dev/null

# --- system should now be inconsistent ---
capture_status system-status
assert_command_fail "partial recovery not detected"
echo "$OUTPUT" | assert_grep "incomplete"
