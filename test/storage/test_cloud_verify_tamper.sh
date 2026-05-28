# Tamper tests for storage-cloud-verify-manifest
#
# Verify that:
#   A. Corrupted encrypted archive → verify fails
#   B. Modified manifest content    → verify fails (minisign catches it)
#
# Both tests share a single pack + two independent encrypt+sign chains.

WORKSPACE="$TMP/cloud_tamper"
mkdir -p "$WORKSPACE"/src/20260528
mkdir -p "$WORKSPACE"/out_a "$WORKSPACE"/out_b

echo "tamper test data" > "$WORKSPACE"/src/20260528/test.zfs
STREAM_CHECKSUM=$(sha256sum "$WORKSPACE"/src/20260528/test.zfs | cut -d' ' -f1)
STREAM_SIZE=$(stat -c%s "$WORKSPACE"/src/20260528/test.zfs)

cat > "$WORKSPACE"/src/20260528/test.zfs.manifest <<EOF
{
    "stream": "test.zfs",
    "snapshot": "cloud-tamper-test@snap",
    "source": "tank/test/active/pile-readonly",
    "guid": "12345",
    "checksum": "$STREAM_CHECKSUM",
    "size": $STREAM_SIZE,
    "created": "2026-05-28T12:00:00+00:00"
}
EOF

# ---- Pack (shared) ----
capture_status pilo storage-cloud-pack \
    "$WORKSPACE"/src/20260528 "$WORKSPACE"/out_a
assert_command_ok
ARCHIVE_PATH=$(echo "$OUTPUT" | tail -1)
[ -n "$ARCHIVE_PATH" ] || fail "empty archive path from pack"

# Copy archive to out_b so both chains start from the same pack
cp "$ARCHIVE_PATH" "$WORKSPACE"/out_b/
cp "${ARCHIVE_PATH}.manifest" "$WORKSPACE"/out_b/

# ---- Keys (shared) ----
AGE_KEY="$WORKSPACE"/age.key
age-keygen -o "$AGE_KEY" 2>/dev/null
AGE_RECIPIENT=$(age-keygen -y "$AGE_KEY" 2>/dev/null)

MINISIGN_KEY="$WORKSPACE"/minisign.key
MINISIGN_PUB="$WORKSPACE"/minisign.pub
minisign -G -s "$MINISIGN_KEY" -p "$MINISIGN_PUB" -W -f 2>/dev/null
MINISIGN_PUBKEY=$(tail -1 < "$MINISIGN_PUB")

# ---- Encrypt A ----
capture_status pilo storage-cloud-encrypt \
    "$AGE_RECIPIENT" "$WORKSPACE"/out_a/*.tar.zst "$WORKSPACE"/out_a
assert_command_ok
ENC_A=$(echo "$OUTPUT" | tail -1)
MAN_A="${ENC_A}.manifest"

# Sign A
capture_status pilo storage-cloud-sign-manifest \
    "$MINISIGN_KEY" "$MAN_A"
assert_command_ok

# ---- Encrypt B ----
capture_status pilo storage-cloud-encrypt \
    "$AGE_RECIPIENT" "$WORKSPACE"/out_b/*.tar.zst "$WORKSPACE"/out_b
assert_command_ok
ENC_B=$(echo "$OUTPUT" | tail -1)
MAN_B="${ENC_B}.manifest"

# Sign B
capture_status pilo storage-cloud-sign-manifest \
    "$MINISIGN_KEY" "$MAN_B"
assert_command_ok

# ================================================================
# Test A: tamper with the encrypted archive
# ================================================================
# Corrupt the first few bytes of the encrypted archive
dd if=/dev/urandom bs=1 count=64 of="$ENC_A" conv=notrunc 2>/dev/null

capture_status pilo storage-cloud-verify-manifest \
    "$MINISIGN_PUBKEY" "$MAN_A"
assert_command_fail
echo "$OUTPUT" | assert_grep "ERROR:"

# ================================================================
# Test B: modify the manifest content (breaks minisign signature)
# ================================================================
# Overwrite a field directly (same byte count to avoid alignment issues)
sed -i 's/"version": 1/"version": 2/' "$MAN_B"

capture_status pilo storage-cloud-verify-manifest \
    "$MINISIGN_PUBKEY" "$MAN_B"
assert_command_fail
echo "$OUTPUT" | assert_grep "ERROR:"
