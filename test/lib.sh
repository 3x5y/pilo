#!/bin/sh

capture_status() {
    set +e
    OUTPUT=$("$@" 2>&1)
    STATUS=$?
    set -e
}

fail() {
    echo "FAIL:" "$@"
    exit 1
}

assert_file_exists() {
    [ -f "$1" ] || fail "expected file missing: $1" 
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
