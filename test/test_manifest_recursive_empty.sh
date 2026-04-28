#!/bin/sh
set -e

rm -rf /$PILE/* 2>/dev/null || true

system-manifest-update

# must not fail
system-manifest-verify
