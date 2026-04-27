#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

with_writable $PILE mkdir -p /$PILE/out/collection/foo

system-prune-pile

[ ! -d /$PILE/out/collection/foo ] \
    || fail "empty directory not pruned"
