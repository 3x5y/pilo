#!/bin/sh
set -e

# Create content and a canonical snapshot
echo "content" > /$ADMIN/file.txt
pilo snapshot-rpo

# Seed the replica
pilo replica-seed

# More content, another snapshot, then replicate with stream export
echo "more" > /$ADMIN/file2.txt
pilo snapshot-rpo
PILO_STREAM_EXPORT=1 pilo replicate

# Find the latest canonical snapshot
latest_snap=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-incr$" | tail -1)
snap_name=${latest_snap#*@}
ts=${snap_name%%-*}
date_dir=$(echo "$ts" | cut -c1-8)
stream_file=$PILO_STREAM_OUTPUT_PATH/$date_dir/$snap_name.zfs
manifest_file=${stream_file}.manifest

# Assert stream artefacts exist
assert_file_exists "$stream_file"
assert_file_exists "$manifest_file"

# Verify via stream-verify
capture_status pilo stream-verify "$stream_file"
assert_command_ok

capture_status pilo stream-verify "$manifest_file"
assert_command_ok
