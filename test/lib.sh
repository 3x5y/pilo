#!/bin/sh

capture_status() {
    set +e
    OUTPUT=$("$@" 2>&1)
    STATUS=$?
    set -e
}

