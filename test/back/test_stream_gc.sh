#!/bin/sh
set -e

echo "content1" > /$ADMIN/file1.txt

# Create a mark and seed (places hold on the mark)
pilo snapshot-mark
MARK=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-mark$" | tail -1)
MARK=${MARK#*@}

pilo replica-seed

# Determine cutoff boundary from the mark's timestamp
CUTOFF_TS=${MARK%%-*}

# Create a fake stream file in a date dir BEFORE the cutoff
# (assume we are running post-2001)
PREV_TS=20010101_000000_000000
PREV_DATE=20010101
mkdir -p "$PILO_STREAM_OUTPUT_PATH/$PREV_DATE"
OLD_STREAM="$PILO_STREAM_OUTPUT_PATH/$PREV_DATE/${PREV_TS}-reg.zfs"
touch "$OLD_STREAM"
touch "$OLD_STREAM.manifest"

# Create a fake stream file in a date dir AFTER the cutoff
POST_TS=$(echo "$CUTOFF_TS" | awk -F_ '{printf "%s_%s_%s_%06d", $1, $2, $3, $4 + 1}')
POST_DATE=$(echo "$POST_TS" | cut -c1-8)
mkdir -p "$PILO_STREAM_OUTPUT_PATH/$POST_DATE"
NEW_STREAM="$PILO_STREAM_OUTPUT_PATH/$POST_DATE/${POST_TS}-reg.zfs"
touch "$NEW_STREAM"
touch "$NEW_STREAM.manifest"

# Assert both exist before GC
assert_file_exists "$OLD_STREAM"
assert_file_exists "$OLD_STREAM.manifest"
assert_file_exists "$NEW_STREAM"
assert_file_exists "$NEW_STREAM.manifest"

# Run stream-gc with GC path
GC_TRASH="$TMP/gc_trash"
export PILO_STREAM_GC_PATH="$GC_TRASH"
capture_status pilo stream-gc
assert_command_ok
echo "$OUTPUT" | assert_grep "PRUNE $OLD_STREAM"

# Assert old stream moved to trash
assert_file_exists "$GC_TRASH/$PREV_DATE/${PREV_TS}-reg.zfs"
assert_file_exists "$GC_TRASH/$PREV_DATE/${PREV_TS}-reg.zfs.manifest"
# Assert old stream no longer in output
test ! -f "$OLD_STREAM" || { echo "old stream not pruned"; exit 1; }
test ! -f "$OLD_STREAM.manifest" || { echo "old manifest not pruned"; exit 1; }

# Assert new stream still in output
assert_file_exists "$NEW_STREAM"
assert_file_exists "$NEW_STREAM.manifest"
