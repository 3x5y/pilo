#!/bin/sh
set -e

zfs list | grep -q "tank/data/active/pile" || exit 1
zfs list | grep -q "tank/data/archive" || exit 1
zfs list | grep -q "tank/data/spool" || exit 1
zfs list | grep -q "tank/data/stash" || exit 1
