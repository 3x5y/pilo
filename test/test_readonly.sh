#!/bin/sh
set -e

DATASET="$TEST_ROOT/active/pile-readonly"

system-init

if (echo data > /$DATASET/test.txt) 2>/dev/null
then
    fail write succeeded on readonly dataset
fi
