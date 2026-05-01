#!/bin/sh
set -eu

ts=$(date +%Y%m%d_%H%M%S_%N)

zfs snapshot -r "$PILO_ROOT@a-$ts"
