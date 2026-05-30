#!/bin/sh
set -e

# Cloud GC lifecycle with stream-gc interaction.
#
# Scenario:
#   1. Old streams (pre-epoch) + cloud export (pack/encrypt/sign)
#   2. Mark snapshot + replica seed (held mark for stream GC cutoff)
#   3. New streams (post-mark) + cloud export
#   4. Stream GC prunes old streams
#   5. Cloud GC preview → old REMOVE / new KEEP
#   6. Cloud GC execute → old export files deleted, new retained

WORKSPACE="$TMP/cloud_gc_lifecycle"
STREAM_ROOT="$PILO_STREAM_OUTPUT_PATH"
CLOUD_ROOT="$WORKSPACE/cloud"
mkdir -p "$WORKSPACE" "$CLOUD_ROOT"

# ---- Age key ----
AGE_KEY="$WORKSPACE/age.key"
age-keygen -o "$AGE_KEY" 2>/dev/null
[ -f "$AGE_KEY" ] || fail "age key not created"
AGE_RECIPIENT=$(age-keygen -y "$AGE_KEY" 2>/dev/null)
[ -n "$AGE_RECIPIENT" ] || fail "empty age recipient"

# ---- Minisign key ----
MINISIGN_KEY="$WORKSPACE/minisign.key"
MINISIGN_PUB="$WORKSPACE/minisign.pub"
minisign -G -s "$MINISIGN_KEY" -p "$MINISIGN_PUB" -W -f >/dev/null
[ -f "$MINISIGN_KEY" ] || fail "minisign secret key not created"
MINISIGN_PUBKEY=$(tail -1 < "$MINISIGN_PUB")
[ -n "$MINISIGN_PUBKEY" ] || fail "empty minisign pubkey"

# =====================================================
# Step 1: Old stream files (pre-mark epoch)
# =====================================================
OLD_TS=20010101_000000_000000
OLD_DATE=20010101
OLD_STREAM_DIR="$STREAM_ROOT/$OLD_DATE"
mkdir -p "$OLD_STREAM_DIR"

echo "old-stream-data" > "$OLD_STREAM_DIR/${OLD_TS}-reg.zfs"
OLD_CHECKSUM=$(sha256sum "$OLD_STREAM_DIR/${OLD_TS}-reg.zfs" | cut -d' ' -f1)
OLD_SIZE=$(stat -c%s "$OLD_STREAM_DIR/${OLD_TS}-reg.zfs")

cat > "$OLD_STREAM_DIR/${OLD_TS}-reg.zfs.manifest" <<EOF
{
    "stream": "${OLD_TS}-reg.zfs",
    "snapshot": "${OLD_TS}-reg",
    "source": "tank/test/active/pile-readonly",
    "guid": "old-guid-1",
    "checksum": "$OLD_CHECKSUM",
    "size": $OLD_SIZE,
    "created": "2001-01-01T00:00:00+00:00"
}
EOF

# =====================================================
# Step 2: Old cloud export (pack → encrypt → sign)
# =====================================================
capture_status pilo storage-cloud-pack \
    "$STREAM_ROOT" "$CLOUD_ROOT"
assert_command_ok
OLD_ARCHIVE=$(echo "$OUTPUT" | tail -1)
[ -n "$OLD_ARCHIVE" ] || fail "empty archive path from old pack"
assert_file_exists "$OLD_ARCHIVE"
assert_file_exists "${OLD_ARCHIVE}.manifest"

capture_status pilo storage-cloud-encrypt \
    "$AGE_RECIPIENT" "$OLD_ARCHIVE" "$CLOUD_ROOT"
assert_command_ok
OLD_ENC_ARCHIVE=$(echo "$OUTPUT" | tail -1)
assert_file_exists "$OLD_ENC_ARCHIVE"
OLD_CLOUD_MANIFEST="${OLD_ENC_ARCHIVE}.manifest"
assert_file_exists "$OLD_CLOUD_MANIFEST"

capture_status pilo storage-cloud-sign-manifest \
    "$MINISIGN_KEY" "$OLD_CLOUD_MANIFEST"
assert_command_ok
assert_file_exists "${OLD_CLOUD_MANIFEST}.minisig"

OLD_STAMP=$(basename "$OLD_ENC_ARCHIVE" .tar.zst.age)

# Ensure next pack runs in a different second to avoid stamp collision
sleep 1

# =====================================================
# Step 3: Held mark snapshot (stream GC cutoff)
# =====================================================
pilo storage-snapshot-mark
pilo storage-replica-seed

MARK=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-mark$" | tail -1)
MARK=${MARK#*@}
CUTOFF_TS=${MARK%%-*}

# =====================================================
# Step 4: New stream files (post-mark)
# =====================================================
POST_TS=$(echo "$CUTOFF_TS" | awk -F_ '{printf "%s_%s_%s_%06d", $1, $2, $3, $4 + 1}')
POST_DATE=$(echo "$POST_TS" | cut -c1-8)
NEW_STREAM_DIR="$STREAM_ROOT/$POST_DATE"
mkdir -p "$NEW_STREAM_DIR"

echo "new-stream-data" > "$NEW_STREAM_DIR/${POST_TS}-reg.zfs"
NEW_CHECKSUM=$(sha256sum "$NEW_STREAM_DIR/${POST_TS}-reg.zfs" | cut -d' ' -f1)
NEW_SIZE=$(stat -c%s "$NEW_STREAM_DIR/${POST_TS}-reg.zfs")

cat > "$NEW_STREAM_DIR/${POST_TS}-reg.zfs.manifest" <<EOF
{
    "stream": "${POST_TS}-reg.zfs",
    "snapshot": "${POST_TS}-reg",
    "source": "tank/test/active/pile-readonly",
    "guid": "new-guid-1",
    "checksum": "$NEW_CHECKSUM",
    "size": $NEW_SIZE,
    "created": "$(date -Iseconds)"
}
EOF

# =====================================================
# Step 5: New cloud export (old streams already exported)
# =====================================================
capture_status pilo storage-cloud-pack \
    "$STREAM_ROOT" "$CLOUD_ROOT"
assert_command_ok
NEW_ARCHIVE=$(echo "$OUTPUT" | tail -1)
[ -n "$NEW_ARCHIVE" ] || fail "empty archive path from new pack"
assert_file_exists "$NEW_ARCHIVE"
assert_file_exists "${NEW_ARCHIVE}.manifest"

capture_status pilo storage-cloud-encrypt \
    "$AGE_RECIPIENT" "$NEW_ARCHIVE" "$CLOUD_ROOT"
assert_command_ok
NEW_ENC_ARCHIVE=$(echo "$OUTPUT" | tail -1)
assert_file_exists "$NEW_ENC_ARCHIVE"
NEW_CLOUD_MANIFEST="${NEW_ENC_ARCHIVE}.manifest"
assert_file_exists "$NEW_CLOUD_MANIFEST"

capture_status pilo storage-cloud-sign-manifest \
    "$MINISIGN_KEY" "$NEW_CLOUD_MANIFEST"
assert_command_ok
assert_file_exists "${NEW_CLOUD_MANIFEST}.minisig"

NEW_STAMP=$(basename "$NEW_ENC_ARCHIVE" .tar.zst.age)

# =====================================================
# Step 6: Stream GC — prunes old streams
# =====================================================
GC_TRASH="$WORKSPACE/gc_trash"
export PILO_STREAM_GC_PATH="$GC_TRASH"
capture_status pilo storage-stream-gc
assert_command_ok

# Old streams gone from output directory
test ! -f "$OLD_STREAM_DIR/${OLD_TS}-reg.zfs" \
    || fail "old stream survived stream-gc"
test ! -f "$OLD_STREAM_DIR/${OLD_TS}-reg.zfs.manifest" \
    || fail "old stream manifest survived stream-gc"
# Old streams moved to trash
assert_file_exists "$GC_TRASH/$OLD_DATE/${OLD_TS}-reg.zfs"
assert_file_exists "$GC_TRASH/$OLD_DATE/${OLD_TS}-reg.zfs.manifest"
# New streams survive
assert_file_exists "$NEW_STREAM_DIR/${POST_TS}-reg.zfs"
assert_file_exists "$NEW_STREAM_DIR/${POST_TS}-reg.zfs.manifest"

# =====================================================
# Step 7: Cloud GC — preview (with trash path)
# =====================================================
CLOUD_GC_TRASH="$WORKSPACE/cloud_gc_trash"
mkdir -p "$CLOUD_GC_TRASH"
export PILO_CLOUD_GC_PATH="$CLOUD_GC_TRASH"

capture_status pilo storage-cloud-gc \
    "$STREAM_ROOT" "$CLOUD_ROOT" "$MINISIGN_PUBKEY" --preview
assert_command_ok
echo "$OUTPUT" | assert_grep "REMOVE.*$OLD_STAMP"
echo "$OUTPUT" | assert_grep "KEEP.*$NEW_STAMP"

# =====================================================
# Step 8: Cloud GC — execute
# =====================================================
capture_status pilo storage-cloud-gc \
    "$STREAM_ROOT" "$CLOUD_ROOT" "$MINISIGN_PUBKEY"
assert_command_ok
echo "$OUTPUT" | assert_grep "REMOVED $OLD_STAMP"

# =====================================================
# Step 9: Verify old export moved to trash, new export intact
# =====================================================
test ! -f "$OLD_ENC_ARCHIVE" \
    || fail "old encrypted archive survived cloud-gc"
test ! -f "${OLD_ENC_ARCHIVE}.manifest" \
    || fail "old cloud manifest survived cloud-gc"
test ! -f "${OLD_ENC_ARCHIVE}.manifest.minisig" \
    || fail "old minisig survived cloud-gc"
assert_file_exists "$CLOUD_GC_TRASH/${OLD_STAMP}.tar.zst.age"
assert_file_exists "$CLOUD_GC_TRASH/${OLD_STAMP}.tar.zst.age.manifest"
assert_file_exists "$CLOUD_GC_TRASH/${OLD_STAMP}.tar.zst.age.manifest.minisig"

assert_file_exists "$NEW_ENC_ARCHIVE"
assert_file_exists "${NEW_ENC_ARCHIVE}.manifest"
assert_file_exists "${NEW_ENC_ARCHIVE}.manifest.minisig"
