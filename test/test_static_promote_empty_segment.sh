#!/bin/sh
set -e

file=silly.txt
mkfile data $file
capture_file $file
system-ingest-pile
with_writable $PILE \
    mkdir -p /$PILE/out/filing/
# simulate weird path
with_writable $PILE \
    sh -c "mv /$PILE/in/$file /$PILE/out/filing//$file"
# FIXME this test is pointless
capture_status system-static-promote

assert_command_fail
