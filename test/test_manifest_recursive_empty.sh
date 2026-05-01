#!/bin/sh
set -e

rm -rf /$PILE/* 2>/dev/null || true

pilo manifest-update

# must not fail
pilo manifest-verify
