#!/bin/sh
set -eu

HERE=$(realpath "$(dirname $0)")

NAME=pilo0
IMAGE=ubuntu:r
MOUNT=/mnt
MEMORY=8GiB
CPUS=4

do_create() {
    lxc init --vm $IMAGE $NAME
    lxc config device add $NAME src disk source=$HERE path=/mnt
    lxc config set $NAME limits.memory $MEMORY
    lxc config set $NAME limits.cpu $CPUS
    do_start
}

do_start() {
    count=10
    lxc start $NAME
    printf "starting "
    while true
    do
        sleep 1
        if lxc exec $NAME true 2>/dev/null
        then
            echo . ready
            break
        fi
        if [ $count -eq 0 ]
        then
            echo . timeout waiting to start
            break
        fi
        count=$(expr $count - 1)
        printf .
    done
}

do_stop() {
    lxc stop -f $NAME
}

do_destroy() {
    do_stop
    lxc rm -f $NAME
}

case "$1" in
    --create|--start|--stop|--destroy)
        func=do_${1#--}
        "$func"
        exit
        ;;
    *) ;;
esac

: ${TEST_FAIL_FAST:=}

lxc exec $NAME \
    --env TEST_FAIL_FAST=$TEST_FAIL_FAST \
    --cwd $MOUNT \
    -- "$@"
