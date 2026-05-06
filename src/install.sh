#!/bin/sh

HERE=$(dirname $(readlink -f "$0"))

ln -snfv "$HERE"/pilo.sh /usr/local/bin/pilo

APT_INSTALL="
    git
    tree
    zfsutils-linux
"

export DEBIAN_FRONTEND=noninteractive

apt-get update \
  && apt-get -y upgrade \
  && apt-get -y --no-install-recommends install $APT_INSTALL
  #&& apt-get -y --no-install-recommends install "${APT_INSTALL[@]}"

