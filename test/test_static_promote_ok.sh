#!/bin/sh
set -e

SRC=/tank/data/active/pile-readonly
DST=/tank/data/static/filing/2026

mkdir -p $DST
echo doc > $SRC/test.txt
system-manifest-update

system-static-promote test.txt filing/2026

assert_not_exists $SRC/test.txt "file still in pile"
assert_file_exists $DST/test.txt "file not moved to filing"
