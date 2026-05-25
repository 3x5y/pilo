#!/bin/sh
set -e

echo "content1" > /$ADMIN/file1.txt

# First anchor + seed replica (replica now has A_ANCHOR)
pilo snapshot-mark
A_ANCHOR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-mark$" | tail -1)
A_ANCHOR=${A_ANCHOR#*@}
pilo replica-seed

# First incremental
echo "content2" > /$ADMIN/file2.txt
pilo snapshot-reg
INCR1=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
INCR1=${INCR1#*@}

# Second anchor
echo "content3" > /$ADMIN/file3.txt
pilo snapshot-mark
B_ANCHOR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-mark$" | tail -1)
B_ANCHOR=${B_ANCHOR#*@}

# Second and third incrementals
echo "content4" > /$ADMIN/file4.txt
pilo snapshot-reg
INCR2=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
INCR2=${INCR2#*@}

echo "content5" > /$ADMIN/file5.txt
pilo snapshot-reg
INCR3=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
INCR3=${INCR3#*@}

# Third anchor
echo "content6" > /$ADMIN/file6.txt
pilo snapshot-mark
C_ANCHOR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-mark$" | tail -1)
C_ANCHOR=${C_ANCHOR#*@}

# Build rollup plans and execute
capture_status pilo rollup
assert_command_ok

# Determine rollup filenames
A_TS=${A_ANCHOR%%-*}
B_TS=${B_ANCHOR%%-*}
C_TS=${C_ANCHOR%%-*}
B_DATE=$(echo "$B_TS" | cut -c1-8)
C_DATE=$(echo "$C_TS" | cut -c1-8)
ROLLUP1="$PILO_STREAM_OUTPUT_PATH/${B_DATE}/${A_TS}--${B_TS}.rollup.zfs"
ROLLUP2="$PILO_STREAM_OUTPUT_PATH/${C_DATE}/${B_TS}--${C_TS}.rollup.zfs"

# Assert rollup files exist and verify OK
assert_file_exists "$ROLLUP1"
assert_file_exists "$ROLLUP2"

capture_status pilo stream-verify "$ROLLUP1"
assert_command_ok
capture_status pilo stream-verify "$ROLLUP2"
assert_command_ok

# Replay rollups into seeded replica
capture_status pilo stream-replay-all "$PILO_STREAM_OUTPUT_PATH" "$TEST_REPLICA"
assert_command_ok

# Assert all snapshots exist on replica (rollups should reconstruct
# intermediate incrementals)
for snap in "$A_ANCHOR" "$INCR1" "$B_ANCHOR" "$INCR2" "$INCR3" "$C_ANCHOR"; do
    zfs list -t snapshot -Ho name "$TEST_REPLICA" | assert_grep "$snap"
done
