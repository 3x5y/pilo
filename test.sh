#!/bin/sh

set -e

RED='\e[0;31m'
GREEN='\e[0;32m'
RESET='\e[0m'

echo "[TEST] Running tests"

HERE=$(dirname $0)
for test_file in $HERE/test_*.sh
do
    TEST_NAME=$(basename $test_file)
    echo "[TEST] $test_file"
    if sh $test_file
    then
        echo "[${GREEN}PASS${RESET}] $test_file"
    else
        RESULT=$?
        echo "[${RED}FAIL${RESET}] $test_file"
        exit $RESULT
    fi
done
