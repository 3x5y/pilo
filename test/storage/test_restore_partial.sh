#!/bin/sh
set -e

repl_pile=$TEST_REPLICA/pile
snap=baseline
echo admin-data > /$ADMIN/admin.txt
echo pile-data > /$PILE/in/p.txt
with_writable $STATIC \
    touch /$STATIC/doc.txt
pilo storage-snapshot $snap
pilo storage-replica-seed

clear_holds
zfs destroy -r $TEST_ROOT
zfs create -p $TEST_ROOT/active

# --- recover ONLY pile ---
pilo storage-restore $repl_pile $PILE $snap

# --- system should now be inconsistent ---
capture_status pilo status
assert_command_fail "partial recovery not detected"
echo "$OUTPUT" | assert_grep "missing.required.dataset"
