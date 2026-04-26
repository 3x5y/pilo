#!/bin/sh
set -e

echo x > /tmp/bad.txt
system-capture /tmp/bad.txt
system-ingest-pile

capture_status system-static-promote bad.txt nonsense/path

assert_command_fail invalid destination accepted
