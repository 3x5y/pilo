# pilo — Personal Information Management System

## Entrypoint & dispatch

- `src/pilo.sh` sources config then dispatches `pilo <cmd>` → `src/pilo/cmd/pilo-<cmd>.py`.
- All commands are single-dispatch, one file per command (27 commands).
- Every command calls `error.run_main(main)` which catches `FatalError`.

## Python package

- `src/pilo/` — stdlib only, zero external deps. ZFS via `subprocess` calls.
- Two top-level subpackages: `back/` (replication/recovery), `front/` (capture/ingestion).
- Key modules: `context.py` (reads env → dataset/path resolution), `paths.py` (logical path parsing, 3 domains: pile/collection/filing), `zfs.py` (thin wrapper over zfs/zpool CLI), `normalize.py` (dataset contract enforcement).

## Storage topology

Three ZFS domains under `$PILO_PRIMARY_ROOT`:
- `active/pile-readonly` (in/out/sort subdirs) — mutable intake, read-only dataset
- `static/collection` — topic-based, read-only
- `static/filing/<year>` — date-based

All canonical datasets enumerated in `normalize.py:dataset_contracts` with expected readonly/mountpoint/canmount properties.

Replication targets via `$PILO_SECONDARY_ROOTS` (space-separated label/root pairs).

## Config (first-match wins)

1. `$PILO_CONFIG` env → shell file path
2. `/etc/pilo.conf.sh`
3. `src/pilo.conf.sh`

Required: `PILO_PRIMARY_ROOT`, `PILO_PATH`, `PILO_USER`. Derived defaults: `PILO_ADMIN_PATH`, `PILO_INTAKE_PATH`, `PILO_PILE_PATH`, `PILO_STATIC_PATH`.

## Tests

Run from repo root. `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=src` set automatically.

**Unit tests** (no ZFS needed):
```
./run-tests.sh --unit                          # all
./run-tests.sh --unit -k test_foo              # single pattern
PYTHONPATH=src:test python3 -B -m unittest test/unit/test_foo.py  # direct
```
Uses `unittest.mock` for ZFS calls. Helper in `test/pilotest.py`: `make_context()`, `import_command()`, `assert_fatal()`.

**System tests** (need root + ZFS):
```
./run-tests.sh --system                                 # all, creates tank/test pool
./run-tests.sh --system test/front/test_foo.sh          # single
TEST_FAIL_FAST=1 ./run-tests.sh --system                # fail fast
```
Each test runs in fresh ZFS hierarchy (`tank/test`). Sources `test/pilotest.sh` for helpers: `mkfile`, `mkintake`, `capture_status`, `assert_file_exists`, `assert_manifest_entry`, `runuser` (runs as `$PILO_USER` via `sudo -u`).

## LXD dev VM

```
./lxc.sh --create       # create + start VM (ubuntu:r, 8GB RAM, 4 CPU)
./lxc.sh <cmd>          # run `pilo <cmd>` inside the VM
./lxc.sh --destroy      # tear down
```
Mounts repo at `/mnt` inside VM.

## Common commands

```
pilo init                           # normalize existing datasets
pilo capture <path>                 # copy file into intake, write manifest
pilo ingest-pile                    # move intake → pile, snapshot
pilo static-promote                 # pile → collection/filing
pilo status                         # system health report
pilo manifest-update                # refresh checksum manifests
pilo manifest-verify                # verify manifests
pilo snapshot                        # ZFS snapshot of all datasets
pilo replicate / pilo replicate-safe
pilo restore                         # restore from replica
pilo rewrite                         # bulk rewrite static paths
pilo stream-export                   # export snapshot to stream file
pilo stream-replay                   # apply stream file to dataset
pilo stream-verify                   # verify stream file checksum
```

## Conventions

- All commands must exit cleanly; errors raise `FatalError` caught by `run_main`.
- Pile datasets are `readonly=on`; use `zfs.dataset_writable()` context manager for mutations.
- Manifests are `sha256sum` files stored in `admin/manifest/`.
