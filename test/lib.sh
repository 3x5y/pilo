#!/bin/sh

### test constants

export ACTIVE=$TEST_ROOT/active
export INTAKE=$TEST_ROOT/active/pile-intake
export PILE=$TEST_ROOT/active/pile-readonly
export STASH=$TEST_ROOT/stash
export STATIC=$TEST_ROOT/static


### setup helpers

mkfile() {
    echo "$1" > $TMP/"$2"
}

mkintake() {
    mkdir -p /$INTAKE/$(dirname "$2")
    echo "$1" > /$INTAKE/"$2"
}

capture_file() {
    system-capture $TMP/"$1"
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
    [ -d "$1" ] || fail "expected file missing: $1" 
}

assert_not_exists() {
    [ ! -e "$1" ] || fail "unexpected path: $1"
}

assert_grep() {
    grep -q "$1" || fail "grep expected: '$1'"
}

assert_not_grep() {
    if grep -q "$1"
    then
        fail "grep found '$1'"
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
    dir="$1"
    entry="$2"
    assert_grep "$entry" < "$dir"/.manifest \
        || fail "missing entry '$entry' in '$dir/.manifest'"
}

assert_manifest_valid() {
    dir="$1"
    (cd "$dir" && sha256sum --quiet --strict -c .manifest) \
        || fail "manifest '$dir/.manifest is invalid"
}
