#!/bin/sh
set -eu

capture_status system status pile

assert_command_ok
