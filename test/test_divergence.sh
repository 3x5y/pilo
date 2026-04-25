#!/bin/sh
set -e

echo pile > /tank/data/active/pile/p.txt
echo archive > /tank/data/archive/a.txt

zfs snapshot tank/data/active/pile@t1

assert_not_exists /tank/data/archive/.zfs/snapshot/t1/a.txt
