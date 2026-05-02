#!/bin/sh
set -e

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TESTLIB="$HERE/test/helpers.sh"

export PATH=$HERE/src:$PATH
ROOT_DATASET=tank/test
TEST_ROOT=$ROOT_DATASET/data
REPLICA_ROOT=$ROOT_DATASET/replica
TEST_REPLICA=$REPLICA_ROOT/data

RED='\e[0;31m'
GREEN='\e[0;32m'
RESET='\e[0m'

RESULT=0

env_setup() {
    TMP_ROOT=$(mktemp -d /tmp/test-XXXXXXXX)
    chmod a+rx $TMP_ROOT
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
    if zfs list $ROOT_DATASET 2>/dev/null 1>&2
    then
        clear_holds
        zfs destroy -r $ROOT_DATASET 2>/dev/null || true
    fi
    zfs create $ROOT_DATASET
    init_system $TEST_ROOT
    init_replica $REPLICA_ROOT
    export TMP="$TMP_ROOT"/$TEST_NAME
    mkdir "$TMP"
    chown $PILO_USER:$PILO_USER "$TMP"
}

clear_holds() {
    for snap in $(zfs list -t snap -d 99999 -Ho name $ROOT_DATASET)
    do
        zfs holds -H $snap \
            | while read ign tag rest
                do
                    zfs release $tag $snap
                done
    done
}

init_system() {
    local root=$1 mount=${2:-}
    if [ "$mount" ]
    then
        zfs create -o mountpoint=$mount $root
    else
        zfs create $root
        mount=/$root
    fi
    export PILO_USER=ubuntu
    export PILO_ROOT=$root
    export PILO_PATH=$mount
    ADMIN=$root/active/admin
    INTAKE=$root/active/pile-intake
    PILE=$root/active/pile-readonly
    STASH=$root/stash
    STATIC=$root/static
    COLLECTION=$root/static/collection
    ADMIN_PATH=$mount/active/admin
    INTAKE_PATH=$mount/active/pile-intake
    PILE_PATH=$mount/active/pile-readonly
    STATIC_PATH=$mount/static
    : "${PILO_ADMIN_PATH:=$ADMIN_PATH}"
    : "${PILO_INTAKE_PATH:=$INTAKE_PATH}"
    : "${PILO_PILE_PATH:=$PILE_PATH}"
    : "${PILO_STATIC_PATH:=$STATIC_PATH}"
    export PILO_ADMIN_PATH
    export PILO_INTAKE_PATH
    export PILO_PILE_PATH
    export PILO_STATIC_PATH
    zfs create -p $ADMIN
    zfs create -p $INTAKE
    zfs create -p $PILE
    zfs create -p $COLLECTION
    chown $PILO_USER:$PILO_USER $PILO_ADMIN_PATH
    chown $PILO_USER:$PILO_USER $PILO_INTAKE_PATH
    chown $PILO_USER:$PILO_USER $PILO_PILE_PATH
    chown $PILO_USER:$PILO_USER $PILO_STATIC_PATH
    #zfs create -p $root/stash
    #zfs create -p $root/static/filing/2025
    pilo init
}

init_replica() {
    export PILO_REPLICA_ROOT=$1/$(basename $PILO_ROOT)
    zfs create -p -o mountpoint=none $1
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
            [ -z "${TEST_FAIL_FAST:-}" ] || break
        fi
    done
}

cmd_clean() {
    zpool_cleanup
    for d in /tmp/test-* /tmp/pilo-tmp-*
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
