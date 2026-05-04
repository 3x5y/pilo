#!/bin/sh
set -e

repl_pile=$TEST_REPLICA/active/pile-readonly
snap=baseline
echo admin-data > /$ADMIN/admin.txt
mkfile pile-data p.txt
capture_file p.txt
pilo ingest-pile
with_writable $STATIC \
    touch /$STATIC/doc.txt
pilo snapshot $snap
pilo replicate

# --- destroy everything ---
zfs destroy -r $TEST_ROOT

# --- recover ONLY pile ---
pilo recover-baseline $repl_pile $PILE $snap >/dev/null

# --- system should now be inconsistent ---
capture_status pilo status
assert_command_fail "partial recovery not detected"
echo "$OUTPUT" | assert_grep "incomplete"
