#!/bin/sh
set -e

FILE="test_admission.txt"

echo "hello world" > /tmp/$FILE

system-capture /tmp/$FILE

if [ ! -f /tank/data/active/pile/$FILE ]
then
    echo "FAIL: file not in canonical location"
    exit 1
fi
