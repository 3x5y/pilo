# PILO Host Installation and Recovery

**DRAFT**

## Purpose

This document describes the three procedures for establishing a PILO host:

1. **Bootstrap:** initialise a new system.
2. **Reinstall:** rebuild the host environment while preserving healthy existing storage.
3. **Recovery:** reconstruct the primary storage tree from a removable secondary.

PILO storage is managed through ZFS. The primary is the canonical working system; removable secondaries provide replicated recovery copies.

These procedures have different starting conditions and must not be substituted for one another.

## 1. Host requirements

Before installing PILO, establish a working Ubuntu system with:

* Administrative access.
* SSH access, as required by the host configuration.
* ZFS utilities.
* Git.
* Python and the dependencies required by PILO.
* The other external utilities required by the installed PILO commands.
* Access to the relevant storage devices and pools.

Install the required dependencies using the repository's host-setup instructions.

The precise dependency list should be maintained alongside the implementation, not duplicated independently across installation documents.

## 2. Installation layout

The expected layout separates installed software, canonical data, and host-local operational state.

| Location          | Purpose                                                        |
| ----------------- | -------------------------------------------------------------- |
| `/opt/pilo`       | Installed PILO source checkout                                 |
| `/z`              | Primary dataset tree, when the primary is imported and mounted |
| `/z/git/pilo.git` | Canonical PILO Git repository                                  |
| `/var/lib/pilo`   | Host-local persistent operational state, if required           |
| `/run`            | Volatile runtime state, such as transient files and locks      |

The actual `/z` mount path and dataset names are determined by the configured PILO environment.

`/opt/pilo` is an installed working checkout. `/z/git/pilo.git` is the canonical repository stored in the PILO dataset tree. They are separate copies with different roles.

## 3. Bootstrap a new system

### Preconditions

* The Ubuntu host is installed and accessible.
* No existing canonical PILO system is being preserved.
* The intended storage devices have been identified.
* The initial PILO source is available from a local worktree or trusted source copy.

### Procedure

1. Install and configure the host operating system.
2. Install PILO's dependencies.
3. Copy the initial PILO source into `/opt/pilo`.
4. Install host configuration, service units, timers, and other required system configuration.
5. Create the primary and secondary ZFS pools.
6. Provision the primary and secondary dataset trees.
7. Initialise the primary storage layout and apply dataset contracts.
8. Initialise the required administrative tooling and Git worktrees.
9. Initialise the pile Git worktree.
10. Create `/z/git/pilo.git` from the initial canonical repository.
11. Verify the canonical repository.
12. Configure `/opt/pilo` to use `/z/git/pilo.git` as its remote.
13. Validate the resulting storage and host configuration.

Use the documented provisioning and initialisation commands. Do not replace existing pools or datasets as part of bootstrap unless their destruction is explicitly intended.

### Completion criteria

* The primary dataset tree satisfies its dataset contracts.
* Required runtime directories and ownership are correct.
* Required manifests and Git repositories exist.
* The canonical repository is accessible.
* PILO validation succeeds.
* Secondary provisioning and initial replication have been tested.

Bootstrap is expected to be performed rarely. Prefer a clear, verified procedure over a heavily automated one.

## 4. Reinstall a host with healthy existing pools

### Preconditions

* The existing primary and canonical repository are healthy.
* The existing storage must be preserved.
* The pool and dataset configuration is known.
* A tested host installation procedure is available.

### Procedure

1. Install or upgrade Ubuntu.
2. Install PILO's dependencies.
3. Import the existing primary pool and make its datasets accessible.
4. Verify that `/z/git/pilo.git` is available.
5. Clone the canonical repository into `/opt/pilo`.
6. Install host configuration, service units, timers, and other required system configuration.
7. Verify the PILO environment and dataset contracts.
8. Run storage, manifest, and replication validation as appropriate.
9. Enable scheduled operations only after validation succeeds.

Do not run bootstrap provisioning or replica seeding merely because the host has been reinstalled.

Reinstallation must not recreate healthy datasets or silently alter replication state.

### Completion criteria

* The existing storage remains intact.
* `/opt/pilo` is installed from the canonical repository.
* Host configuration matches the intended deployment.
* PILO validation succeeds.
* Scheduled operations can run safely.

Test this procedure in a disposable environment before relying on it for a major operating-system upgrade.

## 5. Recover from a secondary

### Preconditions

* The primary is unavailable or has been intentionally removed.
* A usable secondary exists.
* The secondary can be imported independently of the primary.
* The recovery procedure and minimum bootstrap instructions are available.
* The target dataset tree will not overwrite an existing dataset.

### Procedure

1. Install Ubuntu and establish administrative access.
2. Install the dependencies needed to access ZFS, Git, and run PILO.
3. Import the intended secondary pool.
4. Mount or otherwise access the secondary's canonical Git repository read-only.
5. Clone `/z/git/pilo.git` into `/opt/pilo`.
6. Verify that the installed checkout is usable.
7. Unmount the temporary repository access.
8. Install the host configuration needed for recovery.
9. Configure the primary root and secondary roots correctly.
10. Run PILO recovery for the intended target.
11. Run post-recovery validation.
12. Inspect the recovery result and confirm that required datasets and contents are present.
13. Resume normal operation only after the recovered primary has passed validation.

The recovery command must not be treated as successful merely because the restore operation completed. The resulting system must pass the required validation.

Do not seed or reinitialise the secondary as part of recovery unless a separate, explicit procedure calls for it.

### Completion criteria

* The intended target has been restored.
* Required datasets and contents are present.
* Dataset contracts are satisfied.
* Required manifests and runtime directories are valid.
* PILO validation succeeds.
* The recovered primary can be used without modifying the recovery source unintentionally.

## 6. Minimal recovery bootstrap dependency

The full host-setup repository may live inside PILO's canonical repository. Recovery therefore needs a small set of instructions that can be accessed before the primary is restored.

Keep this bootstrap information outside the primary's storage, such as in provisioning documentation or a trusted local copy.

It must identify:

* How to install the minimum required Ubuntu packages.
* How to identify and import the secondary pool.
* How to access the canonical repository on the secondary.
* How to install the PILO checkout.
* How to configure the required environment.
* How to invoke recovery and validate the result.
* The indispensable pool, dataset, and secondary configuration details.

The bootstrap instructions should be sufficient to retrieve the full host-setup repository from the secondary. They should not attempt to duplicate the full host configuration.

Test recovery with the primary unavailable and with no source material available except the secondary and the minimal bootstrap instructions.

## 7. Operational safety

* Never destroy or recreate a pool merely because it is missing from the current host.
* Never use bootstrap provisioning as a substitute for recovery.
* Never seed an existing replica merely because it is behind.
* Do not run rotation GC after a failed replication attempt.
* Do not enable unattended replication until topology detection and replication verification succeed.
* Treat incomplete installation or recovery as an explicit failure requiring inspection.
* Preserve the distinction between storage state and host-local operational state.
