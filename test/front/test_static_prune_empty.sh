#!/bin/sh
set -e

with_writable $PILE \
    mkdir -p /$PILE/out/collection/foo

pilo content-prune

assert_not_exists /$PILE/out/collection/foo
