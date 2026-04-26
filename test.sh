#!/bin/sh

set -e

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TESTLIB="$HERE/test/lib.sh"

export PATH=$HERE/system:$PATH
export TEST_ROOT="tank/data"
export TEST_REPLICA="tank/replica"

RED='\e[0;31m'
GREEN='\e[0;32m'
RESET='\e[0m'

RESULT=0

env_setup() {
    echo "[SETUP] Creating test environment"
    env_teardown
    truncate -s 2G /tmp/vdev1
    truncate -s 2G /tmp/vdev2
    LOOP1=$(losetup --show -f /tmp/vdev1)
    LOOP2=$(losetup --show -f /tmp/vdev2)
    zpool create tank "$LOOP1"
}

env_teardown() {
    zpool destroy -f tank 2>/dev/null || true
    losetup -D 2>/dev/null || true
    rm -f /tmp/vdev* 2>/dev/null || true
}

test_setup() {
    zfs create -p $TEST_ROOT/active/pile-intake
    zfs create -p $TEST_ROOT/active/pile-readonly
    zfs create -p $TEST_ROOT/active/admin
    zfs create -p $TEST_ROOT/archive
    zfs create -p "$TEST_REPLICA"
}

test_teardown() {
    zfs destroy -r "$TEST_ROOT" 2>/dev/null || true
    zfs destroy -r "$TEST_REPLICA" 2>/dev/null || true
}

run_tests() {
    for test_file in "$@"
    do
        test_name=$(basename $test_file .sh)
        [ -e "$test_file" ] || continue
        test_setup
        if (. "$TESTLIB"; . "$test_file")
        then
            echo "[${GREEN}PASS${RESET}] $test_name"
            test_teardown
        else
            RESULT=$?
            echo "[${RED}FAIL${RESET}] $test_name"
            test_teardown
            break
        fi
    done
}

env_setup

if [ -n "$1" ]
then
    run_tests "$@"
else
    run_tests "$HERE/test"/test_*.sh
fi

env_teardown

exit $RESULT
