#!/bin/sh

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
    grep -q "$1" || fail "expected: '$1'"
}

assert_not_grep() {
    grep -v -q "$1" || fail "unexpected: '$1'"
}
