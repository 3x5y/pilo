#!/bin/sh
set -e

pilo storage-init
pilo storage-init

assert_command_ok "init should be idempotent"
