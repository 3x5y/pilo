#!/bin/sh
set -e

mkdir -p /$PILE/out/collection/a/b/c

pilo content-prune

assert_not_exists /$PILE/out/collection/a/b/c
assert_not_exists /$PILE/out/collection/a/b
assert_not_exists /$PILE/out/collection/a
