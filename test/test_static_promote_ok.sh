#!/bin/sh
set -e

SRC=/tank/data/active/pile-readonly
DST=/tank/data/static/collection

echo doc > $SRC/test.txt
system-manifest-update

system-static-promote test.txt collection

assert_not_exists $SRC/test.txt "file still in pile"
assert_file_exists $DST/test.txt "file not moved to filing"
