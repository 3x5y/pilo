#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly

rm -rf $PILE/* 2>/dev/null || true

system-manifest-update

# must not fail
system-manifest-verify
