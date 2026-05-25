#!/bin/sh

# command status

STATUS=0
OUTPUT=''


### setup helpers

reset_system() {
    unset PILO_ADMIN_PATH PILO_INTAKE_PATH PILO_PILE_PATH PILO_STATIC_PATH
    init_system "$@"
}

runuser() {
    sudo -u $PILO_USER env \
        PATH=$PATH \
        PYTHONDONTWRITEBYTECODE=$PYTHONDONTWRITEBYTECODE \
        PILO_PRIMARY_ROOT=$PILO_PRIMARY_ROOT \
        PILO_SECONDARY_ROOTS=$PILO_SECONDARY_ROOTS \
        PILO_PATH=$PILO_PATH \
        PILO_USER=$PILO_USER \
        PILO_ADMIN_PATH=$PILO_ADMIN_PATH \
        PILO_INTAKE_PATH=$PILO_INTAKE_PATH \
        PILO_PILE_PATH=$PILO_PILE_PATH \
        PILO_STATIC_PATH=$PILO_STATIC_PATH \
        "$@"
}

mkfile() {
    echo "$1" > $TMP/"$2"
}

mkintake() {
    mkdir -p /$INTAKE/$(dirname "$2")
    echo "$1" > /$INTAKE/"$2"
}

capture_file() {
    pilo content-capture $TMP/"$1"
}

with_writable() {
    DATASET="$1"
    shift
    zfs set readonly=off "$DATASET"
    "$@"
    RESULT=$?
    zfs set readonly=on "$DATASET"
    return $RESULT
}

capture_status() {
    COMMAND=$(echo "$@")
    if OUTPUT=$("$@" 2>&1)
    then
        STATUS=0
    else
        STATUS=$?
    fi
}


### assert helpers

fail() {
    echo "FAIL:" "$@"
    exit 1
}

assert_file_exists() {
    [ -f "$1" ] || fail "expected file missing: $1" 
}

assert_dir_exists() {
    [ -d "$1" ] || fail "expected dir missing: $1" 
}

assert_not_exists() {
    [ ! -e "$1" ] || fail "unexpected path: $1"
}

assert_grep() {
    grep -q -- "$1" || fail "grep did not match '$1'"
}

assert_not_grep() {
    if grep -q "$1"
    then
        fail "grep matched unwanted '$1'"
    fi
}

assert_command_ok() {
    if [ $STATUS -eq 0 ]
    then
        return
    fi
    echo "$OUTPUT"
    fail "command failed: '$COMMAND'"
}

assert_command_fail() {
    if [ $STATUS -ne 0 ]
    then
        return
    fi
    echo "$OUTPUT"
    fail "command did not fail: '$COMMAND'"
}

assert_manifest_entry() {
    subset="$1"
    entry="$2"
    manifest="$PILO_ADMIN_PATH"/manifest/$subset.manifest
    assert_grep "$entry" < "$manifest" \
        || fail "missing entry '$entry' in '$manifest'"
}

assert_manifest_valid() {
    subset="$1"
    dir="$2"
    manifest="$PILO_ADMIN_PATH"/manifest/$subset.manifest
    (cd "$dir" && sha256sum --quiet --strict -c "$manifest") \
        || fail "manifest $manifest is invalid"
}

assert_owner() {
    local owner="$(stat -c %U "$2")"
    if [ "$owner" != "$1" ]
    then
        fail "path '$2' not owned by $1 (found $owner instead)"
    fi
}
