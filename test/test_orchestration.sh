#!/usr/bin/env bash
set -euo pipefail

#
# Three-cycle rotation:
#
#   primary -> z1 -> z2 -> z1
#
# This exercises:
#
#   1. Initial replica establishment on z1.
#   2. Rotation to a newly attached z2.
#   3. Rotation back to the existing z1 replica after it has been
#      offline for a complete cycle.
#
# The important invariant is that each secondary retains the
# continuity anchors required for its own recovery path, while the
# returning secondary can catch up incrementally.
#

PRI_DEV=/tmp/pilo-orch-z0
PRI_POOL=z0-att
PRI_ROOT=z0-att/pri

SEC_DEV1=/tmp/pilo-orch-z1
SEC_POOL1=z1-rem
SEC_ROOT1=z1-rem/bak
SEC_FS1=z1-rem/bak/pri

SEC_DEV2=/tmp/pilo-orch-z2
SEC_POOL2=z2-rem
SEC_ROOT2=z2-rem/bak
SEC_FS2=z2-rem/bak/pri

export PILO_PRIMARY_ROOT="$PRI_ROOT"
export PILO_SECONDARY_ROOTS="$SEC_FS1 $SEC_FS2"
export PILO_PATH=/z
export PILO_USER=ubuntu

_pilo() {
    echo "# pilo $*" >&2
    pilo "$@"
}

destroy_pool() {
    local pool=$1
    local dev=$2

    zpool destroy -f "$pool" 2>/dev/null || true
    rm -f "$dev"
}

init_pool() {
    local pool=$1
    local dev=$2

    truncate -s 1G "$dev"
    zpool create -m none -O canmount=off "$pool" "$dev"
}

cleanup() {
    destroy_pool "$PRI_POOL" "$PRI_DEV"
    destroy_pool "$SEC_POOL1" "$SEC_DEV1"
    destroy_pool "$SEC_POOL2" "$SEC_DEV2"
}

assert_snapshot() {
    local dataset=$1
    local snap=$2

    zfs list -H -o name "$dataset@$snap" >/dev/null ||
        {
            echo "missing snapshot: $dataset@$snap" >&2
            exit 1
        }
}

assert_no_snapshot() {
    local dataset=$1
    local snap=$2

    if zfs list -H -o name "$dataset@$snap" >/dev/null 2>&1
    then
        echo "unexpected snapshot: $dataset@$snap" >&2
        exit 1
    fi
}

assert_hold() {
    local dataset=$1
    local snap=$2
    local tag=$3

    zfs holds -H "$dataset@$snap" |
        awk -v tag="$tag" '$2 == tag { found=1 } END { exit !found }' ||
        {
            echo "missing hold $tag on $dataset@$snap" >&2
            zfs holds "$dataset@$snap" >&2 || true
            exit 1
        }
}

assert_no_hold() {
    local dataset=$1
    local snap=$2
    local tag=$3

    if zfs holds -H "$dataset@$snap" |
        awk -v tag="$tag" '$2 == tag { found=1 } END { exit found }'
    then
        return
    fi

    echo "unexpected hold $tag on $dataset@$snap" >&2
    zfs holds "$dataset@$snap" >&2 || true
    exit 1
}

rotate_to() {
    local id=$1

    echo "# rotating to $id"

    case "$id" in
        z1)
            zpool export "$SEC_POOL2" 2>/dev/null || true
            zpool import -d /tmp -N "$SEC_POOL1"
            ;;
        z2)
            zpool export "$SEC_POOL1" 2>/dev/null || true
            zpool import -d /tmp -N "$SEC_POOL2"
            ;;
        *)
            echo "invalid secondary: $id" >&2
            exit 1
            ;;
    esac
}

setup() {
    cleanup

    #
    # Primary.
    #
    init_pool "$PRI_POOL" "$PRI_DEV"
    _pilo storage-provision-primary
    _pilo storage-init

    #
    # Provision both removable secondaries while each is attached
    # individually. Leave neither attached at the end.
    #
    init_pool "$SEC_POOL1" "$SEC_DEV1"
    _pilo storage-provision-secondary "$SEC_ROOT1"
    zpool export "$SEC_POOL1"

    init_pool "$SEC_POOL2" "$SEC_DEV2"
    _pilo storage-provision-secondary "$SEC_ROOT2"
    zpool export "$SEC_POOL2"
}

cycle_z1_initial() {
    echo
    echo "=== cycle 1: primary -> z1 ==="
    echo

    rotate_to z1

    _pilo storage-snapshot t0
    _pilo storage-replica-seed

    assert_snapshot "$SEC_FS1" t0
    assert_hold "$PRI_ROOT" t0 pilo:z1-rem
    assert_hold "$SEC_FS1" t0 pilo:z1-rem

    #
    # Advance the primary while z1 is active.
    #
    _pilo storage-snapshot t1
    _pilo storage-replicate

    assert_snapshot "$SEC_FS1" t1
    assert_hold "$PRI_ROOT" t1 pilo:z1-rem
    assert_hold "$SEC_FS1" t1 pilo:z1-rem

    #
    # Age z1. With keep=1, t0 is no longer required by the
    # currently active z1 continuity chain.
    #
    _pilo storage-rotate-gc

    assert_snapshot "$SEC_FS1" t1
    assert_hold "$SEC_FS1" t1 pilo:z1-rem

    #
    # t0 may now have been aged away from the primary and z1.
    #
    #assert_no_snapshot "$PRI_ROOT" t0
    #assert_no_snapshot "$SEC_FS1" t0
}

cycle_z2() {
    echo
    echo "=== cycle 2: z1 -> z2 ==="
    echo

    rotate_to z2

    #
    # z2 is a newly provisioned replica, so it is seeded from the
    # current primary state.
    #
    _pilo storage-replica-seed

    assert_snapshot "$SEC_FS2" t1
    assert_hold "$PRI_ROOT" t1 pilo:z2-rem
    assert_hold "$SEC_FS2" t1 pilo:z2-rem

    #
    # Advance primary while z2 is active.
    #
    _pilo storage-snapshot t2
    _pilo storage-replicate

    assert_snapshot "$SEC_FS2" t2
    assert_hold "$PRI_ROOT" t2 pilo:z2-rem
    assert_hold "$SEC_FS2" t2 pilo:z2-rem

    #
    # z1 is detached and must retain its own continuity anchor.
    #
    # (disabled: $SEC_FS1 is detached!)
    #assert_snapshot "$SEC_FS1" t1
    #assert_hold "$SEC_FS1" t1 pilo:z1-rem

    #
    # Age z2.
    #
    _pilo storage-rotate-gc

    assert_snapshot "$SEC_FS2" t2
    assert_hold "$SEC_FS2" t2 pilo:z2-rem

    #
    # z1's old replica state must be unaffected by z2 GC.
    #
    # (disabled: $SEC_FS1 is detached! asserted in next phase below)
    #assert_snapshot "$SEC_FS1" t1
    #assert_hold "$SEC_FS1" t1 pilo:z1-rem
}

cycle_z1_return() {
    echo
    echo "=== cycle 3: z2 -> z1 ==="
    echo

    rotate_to z1

    #
    # z1's old replica state must be unaffected by z2 GC.
    #
    assert_snapshot "$SEC_FS1" t1
    assert_hold "$SEC_FS1" t1 pilo:z1-rem

    #
    # z1 is an existing replica. It has t1, while the primary has
    # advanced to t2. Normal replication must therefore catch z1
    # up incrementally rather than reseeding it.
    #
    (_pilo storage-replication-verify || true) | grep STATUS=BEHIND
    _pilo storage-replicate
    _pilo storage-replication-verify

    #
    # z1 must now contain the current primary snapshot.
    #
    assert_snapshot "$SEC_FS1" t2
    assert_hold "$PRI_ROOT" t2 pilo:z1-rem
    assert_hold "$SEC_FS1" t2 pilo:z1-rem

    #
    # z2 remains detached and must retain its own continuity anchor.
    #
    # (disabled: $SEC_FS2 is detached!)
    #assert_snapshot "$SEC_FS2" t2
    #assert_hold "$SEC_FS2" t2 pilo:z2-rem

    #
    # Age the returning z1 replica.
    #
    _pilo storage-rotate-gc

    assert_snapshot "$SEC_FS1" t2
    assert_hold "$SEC_FS1" t2 pilo:z1-rem

    #
    # The z2 replica's continuity state remains intact even though
    # z1 is now the active secondary.
    #
    zpool export "$SEC_POOL1"
    zpool import -d /tmp -N "$SEC_POOL2"

    assert_snapshot "$SEC_FS2" t2
    assert_hold "$SEC_FS2" t2 pilo:z2-rem

    echo
    echo "PASS: three-cycle rotation continuity preserved"
}

test_main() {
    setup

    cycle_z1_initial
    cycle_z2
    cycle_z1_return
}

trap cleanup EXIT

test_main
