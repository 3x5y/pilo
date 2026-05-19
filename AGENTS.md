# pilo — Personal Information Management System

## Repo map

- `src/pilo.sh` — shell entrypoint. Resolves `pilo <cmd>` to `src/pilo/cmd/pilo-<cmd>.py`.
- `src/pilo/` — Python package (no external deps, stdlib + ZFS only).
- `src/pilo/cmd/pilo-*.py` — CLI commands (one file per command).
- `doc/specification.md` — full spec, `doc/chat.md` — design log.

## Config

Config is loaded in this order (first match wins):
1. `$PILO_CONFIG` env pointing to a shell file
2. `/etc/pilo.conf.sh`
3. `src/pilo.conf.sh` (in-repo default)

Required env vars: `PILO_PRIMARY_ROOT`, `PILO_PATH`, `PILO_USER`.

## Commands

All commands: `pilo <name> [args...]`. No subcommands beyond single dispatch.
Common commands: `capture`, `ingest-pile`, `static-promote`, `manifest-update`, `manifest-verify`, `status`, `init`, `snapshot`, `replicate`, `restore`, `rewrite`, `replace`.

## Tests

Two test suites, both run from repo root:

**Unit tests (Python unittest):**
```
./run-tests.sh --unit                            # all
./run-tests.sh --unit -k test_foo                # single test pattern
PYTHONPATH=src:test python3 -m unittest test/unit/test_foo.py  # direct
```
`PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=src` are always expected.

**Front-end / integration tests (shell, need root + ZFS):**
```
./run-tests.sh --system                           # all (creates ZFS pool)
./run-tests.sh --system test/front/test_foo.sh    # single
TEST_FAIL_FAST=1 ./run-tests.sh --system          # fail fast
```
Each test runs in a fresh ZFS dataset hierarchy (`tank/test`). Tests source `test/pilotest.sh` for helpers: `mkfile`, `mkintake`, `capture_status`, `assert_file_exists`, `assert_manifest_entry`, `assert_command_ok`, `runuser`. Always run as root (they create ZFS pools).

## Development VM

`lxc.sh` manages a LXD VM for development:
- `lxc.sh --create` — create and start VM
- `lxc.sh --destroy` — tear down
- `lxc.sh <cmd>` — execute `src/pilo.sh <cmd>` inside the VM

## Architecture notes

- Three ZFS storage domains: `pile` (under `active/pile-readonly`), `collection` (under `static/collection`), `filing` (under `static/filing/<year>`).
- Pile subdirectories: `in/`, `out/`, `sort/`.
- Integrity via `sha256sum` manifest files stored in `admin/manifest/`.
- All datasets under primary root. Secondary replica roots for backup.
- Pile datasets are read-only (set via ZFS `readonly=on`).
- Commands run as `PILO_USER` via `sudo -u` in tests (default: `ubuntu`).
