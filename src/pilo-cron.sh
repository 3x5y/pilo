#!/bin/bash

set -euo pipefail

get_time() { date +%Y%m%d%H%M; }

LOCK_FILE=/run/pilo.lock
TRIGGER_FILE=/run/pilo.trigger


if [ "${1:-}" = trigger ]
then
    [ -e $TRIGGER_FILE ] || touch $TRIGGER_FILE
    exit 0
fi


THIS_MINUTE=$(get_time)
TRIGGERED=0

while [ $(get_time) = $THIS_MINUTE ]
do
    if [ -e $LOCK_FILE ]
    then
        break
    fi

    if [ -e $TRIGGER_FILE ]
    then
        TRIGGERED=1
        break
    fi
    sleep 1
done

if [ $TRIGGERED -eq 1 ]
then
    touch $LOCK_FILE
    rm $TRIGGER_FILE
    pilo storage-snapshot-reg
    pilo storage-replicate
    rm $LOCK_FILE
fi
