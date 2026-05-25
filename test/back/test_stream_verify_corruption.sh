#!/bin/sh
set -e

# Same setup as stream_export to produce a clean stream file
echo "data" > /$ADMIN/file.txt
pilo snapshot-reg
pilo replica-seed

echo "more" > /$ADMIN/file2.txt
pilo snapshot-reg
PILO_STREAM_EXPORT=1 pilo replicate

# Find stream file
latest_snap=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
snap_name=${latest_snap#*@}
ts=${snap_name%%-*}
date_dir=$(echo "$ts" | cut -c1-8)
stream_file=$PILO_STREAM_OUTPUT_PATH/$date_dir/$snap_name.zfs
manifest_file=${stream_file}.manifest

# Verify stream is clean first
capture_status pilo stream-verify "$manifest_file"
assert_command_ok

# Corrupt the stream file
echo "garbage" >> "$stream_file"

# Verify corruption is detected
capture_status pilo stream-verify "$manifest_file"
assert_command_fail
echo "$OUTPUT" | assert_grep MISMATCH
