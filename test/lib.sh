#!/bin/sh

### test constants

export INTAKE=tank/data/active/pile-intake
export PILE=tank/data/active/pile-readonly
export STATIC=tank/data/static


### setup helpers

mkfile() {
    echo "$1" > $TMP/$2
}

mkintake() {
    mkdir -p /$INTAKE/$(dirname "$2")
    echo "$1" > /$INTAKE/$2
}

capture_file() {
    system-capture $TMP/$1
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
    fail "command failed:" "$@"
}

assert_command_fail() {
    if [ $STATUS -ne 0 ]
    then
        return
    fi
    echo "$OUTPUT"
    fail "command did not fail:" "$@"
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
