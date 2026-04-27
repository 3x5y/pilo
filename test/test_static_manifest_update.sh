#!/bin/sh
set -e

DST=/tank/data/static/collection

echo important > /tmp/item.txt
system-capture /tmp/item.txt
system-ingest-pile

system-manifest-update

system-static-promote in/item.txt collection

assert_grep item.txt < $DST/.manifest
