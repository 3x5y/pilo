# Full primitive chain: pack → encrypt → sign → verify → decrypt → unpack
#
# All tools invoked via real subprocess (no mocks).

WORKSPACE="$TMP/cloud_chain"
mkdir -p "$WORKSPACE"/src/20260528
mkdir -p "$WORKSPACE"/out

# Create test stream content and manifest
echo "hello world" > "$WORKSPACE"/src/20260528/test.zfs
STREAM_CHECKSUM=$(sha256sum "$WORKSPACE"/src/20260528/test.zfs | cut -d' ' -f1)
STREAM_SIZE=$(stat -c%s "$WORKSPACE"/src/20260528/test.zfs)

cat > "$WORKSPACE"/src/20260528/test.zfs.manifest <<EOF
{
    "stream": "test.zfs",
    "snapshot": "cloud-chain-test@snap",
    "source": "tank/test/active/pile-readonly",
    "guid": "12345",
    "checksum": "$STREAM_CHECKSUM",
    "size": $STREAM_SIZE,
    "created": "2026-05-28T12:00:00+00:00"
}
EOF

# ---- 1. Pack ----
capture_status pilo storage-cloud-pack \
    "$WORKSPACE"/src/20260528 "$WORKSPACE"/out
assert_command_ok
ARCHIVE_PATH=$(echo "$OUTPUT" | tail -1)
[ -n "$ARCHIVE_PATH" ] || fail "empty archive path from pack"
assert_file_exists "$ARCHIVE_PATH"
MANIFEST_PATH="${ARCHIVE_PATH}.manifest"
assert_file_exists "$MANIFEST_PATH"

# ---- 2. Age key generation ----
AGE_KEY="$WORKSPACE"/age.key
age-keygen -o "$AGE_KEY" 2>/dev/null
[ -f "$AGE_KEY" ] || fail "age key not created"
AGE_RECIPIENT=$(age-keygen -y "$AGE_KEY" 2>/dev/null)
[ -n "$AGE_RECIPIENT" ] || fail "empty age recipient"

# ---- 3. Encrypt ----
capture_status pilo storage-cloud-encrypt \
    "$AGE_RECIPIENT" "$ARCHIVE_PATH" "$WORKSPACE"/out
assert_command_ok
ENCRYPTED_PATH=$(echo "$OUTPUT" | tail -1)
assert_file_exists "$ENCRYPTED_PATH"
CLOUD_MANIFEST="${ENCRYPTED_PATH}.manifest"
assert_file_exists "$CLOUD_MANIFEST"

# ---- 4. Minisign key generation ----
MINISIGN_KEY="$WORKSPACE"/minisign.key
MINISIGN_PUB="$WORKSPACE"/minisign.pub
minisign -G -s "$MINISIGN_KEY" -p "$MINISIGN_PUB" -W -f 2>/dev/null
[ -f "$MINISIGN_KEY" ] || fail "minisign secret key not created"
MINISIGN_PUBKEY=$(tail -1 < "$MINISIGN_PUB")
[ -n "$MINISIGN_PUBKEY" ] || fail "empty minisign pubkey"

# ---- 5. Sign ----
capture_status pilo storage-cloud-sign-manifest \
    "$MINISIGN_KEY" "$CLOUD_MANIFEST"
assert_command_ok
SIG_PATH="${CLOUD_MANIFEST}.minisig"
assert_file_exists "$SIG_PATH"

# ---- 6. Verify ----
capture_status pilo storage-cloud-verify-manifest \
    "$MINISIGN_PUBKEY" "$CLOUD_MANIFEST"
assert_command_ok
VERIFIED_PATH=$(echo "$OUTPUT" | tail -1)
[ "$VERIFIED_PATH" = "$ENCRYPTED_PATH" ] \
    || fail "verify returned wrong path: $VERIFIED_PATH != $ENCRYPTED_PATH"

# ---- 7. Decrypt ----
mkdir -p "$WORKSPACE"/decrypted
capture_status pilo storage-cloud-decrypt \
    "$AGE_KEY" "$ENCRYPTED_PATH" "$WORKSPACE"/decrypted
assert_command_ok
DECRYPTED_PATH=$(echo "$OUTPUT" | tail -1)
assert_file_exists "$DECRYPTED_PATH"

# ---- 8. Unpack ----
mkdir -p "$WORKSPACE"/unpacked
capture_status pilo storage-cloud-unpack \
    "$DECRYPTED_PATH" "$WORKSPACE"/unpacked "$CLOUD_MANIFEST"
assert_command_ok
UNPACKED_DIR=$(echo "$OUTPUT" | tail -1)
assert_dir_exists "$UNPACKED_DIR"

# ---- 9. Verify extracted bytes match original ----
assert_file_exists "$UNPACKED_DIR"/test.zfs
assert_file_exists "$UNPACKED_DIR"/test.zfs.manifest

UNPACKED_CHECKSUM=$(sha256sum "$UNPACKED_DIR"/test.zfs | cut -d' ' -f1)
[ "$UNPACKED_CHECKSUM" = "$STREAM_CHECKSUM" ] \
    || fail "content mismatch: $UNPACKED_CHECKSUM != $STREAM_CHECKSUM"
