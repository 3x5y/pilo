#!/bin/sh

APT_INSTALL=(
    zfsutils-linux
)

export DEBIAN_FRONTEND=noninteractive

apt-get update \
  && apt-get -y upgrade \
  && apt-get -y --no-install-recommends install "${APT_INSTALL[@]}"

