#!/bin/sh
: ${TEST_FAIL_FAST:=}
lxc exec pilodev0 \
    --env TEST_FAIL_FAST=$TEST_FAIL_FAST \
    --cwd /src \
    -- "$@"
