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
pilo replica-seed

clear_holds
zfs destroy -r $TEST_ROOT
zfs create -p $TEST_ROOT/active

# --- recover ONLY pile ---
pilo restore $repl_pile $PILE $snap

# --- system should now be inconsistent ---
capture_status pilo status
assert_command_fail "partial recovery not detected"
echo "$OUTPUT" | assert_grep "missing.required.dataset"
