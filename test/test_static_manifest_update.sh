#!/bin/sh
set -e

SRC=/tank/data/active/pile-readonly
DST=/tank/data/static/collection

mkdir -p $DST

echo data > $SRC/item.txt

system-manifest-update

system-static-promote item.txt collection

assert_grep item.txt < $DST/.manifest
