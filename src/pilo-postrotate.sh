#!/usr/bin/env bash
set -Eeuo pipefail

readonly LOCKFILE=/run/lock/pilo-storage.lock
readonly ROTATION_MARKER=/var/lib/pilo/rotation/pending

phase=starting

log() {
    #logger -t pilo-postrotate -- "$*"
    echo "$*"
}

fail() {
    log "Aborted: phase=${phase}: $*"
    printf 'pilo-postrotate: %s\n' "$*" >&2
    exit 1
}

exec 9> "$LOCKFILE"

if ! flock -n 9; then
    fail "another storage operation is active"
fi

if [[ ! -f "$ROTATION_MARKER" ]]; then
    fail "no rotation is pending"
fi

report_fail() {
    rc=$?
    if (( rc != 0 )); then
        log "Failed: phase=${phase}, exit_code=${rc}; rotation marker retained"
    fi
}
trap report_fail EXIT

phase=import-secondary
log "Importing zpools"
zpool import -a

phase=validate-topology
log "Validating attached secondary"
pilo status replication
# Must require exactly one configured secondary attached and a valid topology.

phase=replicate
log "Replicating to attached secondary"
pilo storage-replicate-safe

phase=verify-replication
log "Verifying replication convergence"
pilo storage-replication-verify

phase=rotation-gc
log "Running rotation garbage collection"
pilo storage-rotate-gc
# Must implement the agreed rotation retention plan.

#phase=verify-postconditions
#log "Verifying rotation postconditions"
#pilo storage-rotation-verify
# Must verify the required replication and retention invariants.

phase=clear-marker
log "Clearing rotation marker"
rm -- "$ROTATION_MARKER"

phase=complete
log "Post-rotation completed successfully"
