#!/bin/sh
set -e

FILE=file.txt
TMP=/tmp/$FILE
INTAKE=/tank/data/active/pile-intake/$FILE
CANONICAL=/tank/data/active/pile-readonly/$FILE

echo data > "$TMP"

system-capture "$TMP"

assert_file_exists "$INTAKE"
assert_not_exists "$CANONICAL"
# client copy retained
assert_file_exists "$TMP"
