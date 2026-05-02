#!/bin/sh
set -eu

ts=$(snapshot_timestamp)

zfs snapshot -r "$PILO_ROOT@a-$ts"
