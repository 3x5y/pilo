#!/bin/sh
set -e

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TESTLIB="$HERE/test/lib.sh"

export PATH=$HERE/system:$PATH
export TEST_ROOT="tank/data"
export TEST_REPLICA="tank/replica/data"

RED='\e[0;31m'
GREEN='\e[0;32m'
RESET='\e[0m'

RESULT=0

env_setup() {
    TMP_ROOT=$(mktemp -d /tmp/test-XXXXXXXX)
    USAGE=$(df /tmp | grep -E -o '[0-9]+% /tmp')
    echo "[SETUP] $USAGE TMP_ROOT=$TMP_ROOT"
    zpool_cleanup
    truncate -s 2G /$TMP_ROOT/vdev1
    truncate -s 2G /$TMP_ROOT/vdev2
    LOOP1=$(losetup --show -f /$TMP_ROOT/vdev1)
    LOOP2=$(losetup --show -f /$TMP_ROOT/vdev2)
    zpool create tank "$LOOP1"
}

zpool_cleanup() {
    zpool destroy -f tank 2>/dev/null || true
    losetup -D 2>/dev/null || true
}

env_teardown() {
    if [ "$RESULT" -eq 0 ]
    then
        zpool_cleanup
        #rm -f $TMP_ROOT/vdev* 2>/dev/null || true
        rm -rf "$TMP_ROOT"
    fi
    : # no-op
}

test_setup() {
    zfs destroy -r "$TEST_ROOT" 2>/dev/null || true
    zfs destroy -r "$TEST_REPLICA" 2>/dev/null || true
    zfs create -p $TEST_ROOT/active/pile-intake
    zfs create -p $TEST_ROOT/active/pile-readonly
    zfs create -p $TEST_ROOT/active/admin
    zfs create -p $TEST_ROOT/stash
    zfs create -p $TEST_ROOT/static/collection
    zfs create -p -o readonly=off $TEST_ROOT/static/filing/2025
    zfs create -p "$TEST_REPLICA"
    system-init # FIXME: belongs elsewhere??

    export TMP="$TMP_ROOT"/$TEST_NAME
    mkdir "$TMP"
}

test_teardown() {
    : # no-op
}

run_tests() {
    for test_file in "$@"
    do
        TEST_NAME=$(basename $test_file .sh)
        [ -e "$test_file" ] || continue
        test_setup
        if (. "$TESTLIB"; . "$test_file")
        then
            echo "[${GREEN}PASS${RESET}] $TEST_NAME"
            test_teardown
        else
            RESULT=$?
            echo "[${RED}FAIL${RESET}] $TEST_NAME"
            test_teardown
            break
        fi
    done
}

cmd_clean() {
    zpool_cleanup
    for d in /tmp/test-* /tmp/tmp.*
    do
        echo clean $d
        rm -rf $d
    done
}

cmd_run() {
    env_setup
    if [ "$#" -gt 0 ]
    then
        run_tests "$@"
    else
        run_tests "$HERE/test"/test_*.sh
    fi
    env_teardown
}

usage() {
    echo "Usage: $0 COMMAND"
    echo "Commands"
    echo "  clean"
    echo "  run [tests]"
    exit 1
}

cmd=$1
shift

case "$cmd" in
    clean)
        cmd_clean
        ;;
    run)
        cmd_run "$@"
        ;;
    *)
        usage
        ;;
esac
exit $RESULT
