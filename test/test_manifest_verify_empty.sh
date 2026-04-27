#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly

# ensure empty
rm -f $PILE/* 2>/dev/null || true
rm -f $PILE/.manifest 2>/dev/null || true

system-manifest-update
system-manifest-verify
