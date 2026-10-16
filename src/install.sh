#!/bin/sh

set -eu

HERE=$(dirname $(readlink -f "$0"))
CONFIG=$(readlink -f "$HERE"/../pilo.conf.sh)
. "$CONFIG"

install -v -d -o root -g root -m 0750 /var/lib/pilo/status
install -v -d -o root -g root -m 0750 /var/lib/pilo/rotation
install -v -d -o $PILO_USER -g $PILO_USER -m 0750 /var/lib/pilo/request

ln -snfv "$HERE"/pilo.sh /usr/local/bin/pilo
ln -snfv "$HERE"/pilo-cycle.service /etc/systemd/system
ln -snfv "$HERE"/pilo-cycle.timer /etc/systemd/system
ln -snfv "$HERE"/pilo-cycle.path /etc/systemd/system
ln -snfv "$CONFIG" /etc/pilo.conf.sh

systemctl daemon-reload
#systemctl enable --now pilo-cycle.timer
#systemctl enable --now pilo-cycle.path
