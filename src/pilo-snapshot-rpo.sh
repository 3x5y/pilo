#!/bin/sh
set -eu

ts=$(snapshot_timestamp)
snapshot r-$ts
