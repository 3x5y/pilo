#!/bin/sh
set -eu

require_arg "${1:-}" "require snapshot name"
name="$1"
snapshot "$name"
