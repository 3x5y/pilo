#!/bin/sh
set -eu

name="$1"
[ "$name" ] || fatal "require snapshot name"
snapshot "$name"
