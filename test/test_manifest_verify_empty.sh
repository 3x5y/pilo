#!/bin/sh
set -e

# ensure empty
rm -f /$PILE/* 2>/dev/null || true
rm -f /$PILE/.manifest 2>/dev/null || true

pilo manifest-update
pilo manifest-verify
