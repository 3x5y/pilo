#!/bin/sh
set -e

FILE="test_authority.txt"
TMPFILE="/tmp/$FILE"
CANONICAL="/tank/data/active/pile/$FILE"

echo "authority check" > "$TMPFILE"

system-capture "$TMPFILE"

if [ ! -f "$CANONICAL" ]
then
    echo "FAIL: canonical file missing"
    exit 1
fi

if [ -f "$TMPFILE" ]
then
    echo "FAIL: source file still exists (ambiguous authority)"
    exit 1
fi

REALPATH=$(readlink -f "$CANONICAL")

if [ "$REALPATH" != "$CANONICAL" ]
then
    echo "FAIL: canonical path is indirect or ambiguous"
    exit 1
fi
