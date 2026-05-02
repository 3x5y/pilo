#!/bin/sh
set -eu

ts=$(snapshot_timestamp)
snapshot a-$ts
