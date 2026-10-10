#!/bin/sh

set -eu

HERE=$(dirname $(readlink -f "$0"))
CONFIG=$(readlink -f "$HERE"/../pilo.conf.sh)
. "$CONFIG"

install -d -o root -g root -m 0750 /var/lib/pilo/status
install -d -o root -g root -m 0750 /var/lib/pilo/rotation
install -d -o $PILO_USER -g $PILO_USER -m 0750 /var/lib/pilo/request

ln -sv "$HERE"/pilo.sh /usr/local/bin/pilo
ln -sv "$HERE"/pilo-cycle.service /etc/systemd/system
ln -sv "$HERE"/pilo-cycle.timer /etc/systemd/system
ln -sv "$HERE"/pilo-cycle.path /etc/systemd/system
ln -sv "$CONFIG" /etc/pilo.conf.sh

systemctl daemon-reload
#systemctl enable --now pilo-cycle.timer
#systemctl enable --now pilo-cycle.path
