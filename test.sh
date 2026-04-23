#!/bin/sh

set -e

RED='\e[0;31m'
GREEN='\e[0;32m'
RESET='\e[0m'

echo "[TEST] Running tests"

HERE=$(dirname $0)
for test_file in $HERE/test_*.sh
do
    test_name=$(basename $test_file .sh)
    echo "[TEST] $test_name"
    if sh $test_file
    then
        echo "[${GREEN}PASS${RESET}] $test_name"
    else
        RESULT=$?
        echo "[${RED}FAIL${RESET}] $test_name"
        exit $RESULT
    fi
done
