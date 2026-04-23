#!/bin/sh

set -e

# setup once
zfs create -p tank/data/active/pile

# run tests
sh ./test_admission.sh
sh ./test_snapshot.sh
sh ./test_authority.sh
