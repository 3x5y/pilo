#!/bin/sh
set -e

echo x > /tank/data/active/pile-readonly/bad.txt

capture_status system-static-promote bad.txt nonsense/path

assert_command_fail invalid destination accepted
