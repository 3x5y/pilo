#!/bin/sh

set -e

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LIB=$HERE/testlib.sh
export PATH=$HERE/system:$PATH

RED='\e[0;31m'
GREEN='\e[0;32m'
RESET='\e[0m'

RESULT=0

sh "$HERE"/env_setup.sh

echo "[TEST] Running tests"

for test_file in $HERE/test_*.sh
do
    test_name=$(basename $test_file .sh)
    [ -e "$test_file" ] || continue
    echo "[TEST] $test_name"
    if (. "$LIB"; . "$test_file")
    then
        echo "[${GREEN}PASS${RESET}] $test_name"
    else
        RESULT=$?
        echo "[${RED}FAIL${RESET}] $test_name"
        break
    fi
done

sh "$HERE"/env_teardown.sh

exit $RESULT
