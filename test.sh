#!/bin/sh

set -e

echo "[TEST] Running tests"

sh ./test_admission.sh
sh ./test_snapshot.sh
sh ./test_authority.sh
