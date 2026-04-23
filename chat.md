<!-- vim: set filetype=markdown: -->

## >> User

# CONTEXT CHECKPOINT PROMPT

You are continuing a design discussion for a **personal information management
system** defined by a formal specification.

Your role:

* Act as a critical collaborator
* Preserve conceptual integrity of the system
* Challenge inconsistencies
* Prefer clarity and enforceability over elegance
* Avoid unnecessary abstraction unless it reduces operational ambiguity

---

## SYSTEM OVERVIEW

The system governs how personal information is:

* admitted
* organised
* protected
* retained
* recovered

It prioritises:

* long-term durability
* interpretability
* bounded operational burden
* realistic human behaviour

---

## CORE MODELS

### 1. Information Model

Canonical classes:

1. Administrative Information
2. Project Work
3. Synchronised Communication Streams
4. Static Personal Material
5. Provisional Peripheral Capture

Key properties per class:

* provenance
* canonical authority
* mutation profile
* lifecycle expectation
* protection obligation

Important distinctions:

* Canonical ≠ immutable
* Provisional can still be canonical
* Peripheral capture is explicitly non-canonical

---

### 2. Durability Model

Durability is composed of three layers:

1. **Baseline (Off-site HDD rotation)**

   * Full snapshot
   * Defines recovery anchor

2. **Recent Change Protection (Cloud deltas)**

   * Incremental
   * Multi-provider redundancy
   * Bounded in size and duration

3. **Local Reversibility**

   * Snapshots
   * Version control
   * Append-dominant structures

---

## CRITICAL CLARIFICATIONS

### Authority vs Protection

* **Canonical Authority** = where conflicts resolve (typically server)
* **Durability State** = level of protection (baseline, delta, or none)

These are explicitly NOT the same thing.

---

### Canonical Admission

* Admission establishes **protection obligation**
* It does NOT guarantee immediate durability
* Durability occurs once data enters replication/snapshot pathways

---

### RPO Scope

* RPO (≤ 1 hour) applies ONLY to:

  * reconciled canonical data

* NOT guaranteed for:

  * transient authoritative state (e.g. unpushed work)

---

### Transient State

* Exists during active client-side work
* Temporarily authoritative but:

  * not durable
  * must be reconciled within bounded time

---

### Protection Tiers (Implicit Model)

The system effectively has:

* Tier 0: No protection (true transient / unmanaged)
* Tier 1: Opportunistic (peripheral capture / stash)
* Tier 2: Canonical but not fully replicated
* Tier 3: Fully durable (baseline + delta)

---

## KEY REQUIREMENTS THEMES

### Functional

* Canonical admission and authority enforcement
* Controlled intake (pile)
* Versioned mutation (git)
* Integrity verification (checksums + manifests)
* Baseline + incremental replication
* Recovery (baseline + complete)
* Observability of system state
* Bounded manual burden (including “bounded-craft”)

---

### Non-Functional

* RPO ≤ 1 hour (with stated limitations)
* Baseline rotation ≤ 30 days
* Integrity verification ≤ 90 days
* Recovery time ≤ 72 hours (baseline)
* Human burden constraints
* Storage and bandwidth limits
* Observability requirements

---

## OPERATIONAL PHILOSOPHY

* CLI-first
* Text as control surface
* Automation for repetition
* Human judgement for semantics
* Avoid over-engineering
* Prefer explicit workflows over implicit behaviour

---

## KNOWN DESIGN POSITIONS

* No real-time sync requirement
* No high-availability infrastructure
* No heavy indexing layer (for now)
* Git used for conflict resolution
* ZFS assumed but not mandated
* Two cloud providers for delta redundancy
* HDD rotation defines durability baseline

---

## RECENT DESIGN CLARIFICATIONS

The following have been explicitly added or resolved:

* RPO applies only to reconciled data
* Admission ≠ durability completion
* Incremental replication must be bounded and may require forced rotation
* Observability must surface violations (replication lag, transient age, etc.)
* Recovery establishes new canonical authority
* Service-backed data aims for full-fidelity local mirror
* Secrets assume client compromise is possible
* Conflict resolution delegated to underlying tools (e.g. git)
* Peripheral and transient data have weaker or no integrity guarantees

---

## OPEN DESIGN AREAS (PARTIALLY RESOLVED OR DEFERRED)

* Observability implementation (likely simple CLI/text-based)
* Dataset granularity heuristics (implementation-level)
* Bounded-craft tooling patterns
* Recovery sequencing and dependency ordering
* Semantic drift detection (lightweight, not formalised)

---

## CURRENT TASK CONTEXT

We are transitioning from **specification → implementation strategy**.

Recent focus areas include:

* translating acceptance criteria into executable tests
* applying test-first methodology to infrastructure
* designing validation scenarios (especially recovery)
* ensuring spec is operationally enforceable, not just conceptually sound

---

## EXPECTED RESPONSE STYLE

* Be precise, not verbose
* Call out contradictions directly
* Prefer operational clarity over theoretical purity
* Suggest minimal viable structure before complex systems
* Assume high competence but limited patience for fluff

---

Focus on **implementation strategy, testing methodology, or unresolved design
edges**, depending on the next prompt.

**END CHECKPOINT**

I now want to start working on a concrete implementation using an iterative
test-first methodology. The tests should be derived from the acceptance tests
given in the specification and proceed in small iterations to deliver useful
slices of functionality, and with a full recovery as the ultimate acceptance
test.

The target hardware is a Raspberry Pi 4B with the OS on SD card, an attached USB
SSD as the main data storage and a USB HDD as the mirrored backup target. The
target OS will most likely be Ubuntu for its ZFS support, although I aspire to
migrating to FreeBSD.

I can develop either on an Intel Linux workstation, or a spare Raspberry Pi
(headless), whichever is more convenient.

I want guidance through the whole process, starting from scratch using only the
specification.

Respond with "OK", and I will provide the specification itself in the next
prompt.

## >> Assistant

So we’re really doing this properly instead of duct-taping cron jobs and hoping for the best. How inconveniently disciplined.

OK


## >> User

[pasted spec]

**END SPECIFICATION**

Now where do we start?

## >> Assistant

You’ve built something that reads like it actually expects to survive contact with reality. Annoying. That means we can’t hide behind vague “we’ll figure it out later” optimism.

We start by refusing to build the system.

We build **tests that prove the system exists**, then painfully drag reality into compliance.

---

# 0. First Correction (before you write a single line)

Your acceptance tests are good, but they are **not yet executable**.

Right now they are:

* human-readable
* conceptually precise
* operationally vague

Example problem:

> “data included in snapshot scope”

That’s not testable until you define:

* how snapshot membership is observed
* what command proves inclusion
* what failure looks like

So step zero is:

### → Convert acceptance tests into **executable assertions**

Not code yet. Just **shell-verifiable conditions**.

---

# 1. Define the Smallest Possible System Slice

You want iteration. So resist the urge to implement “the system.”

Pick the **minimum slice that proves the architecture is viable**:

### Slice 1: Canonical Admission → Snapshot → Recovery (local only)

No cloud. No HDD rotation. No email. No pile complexity.

Just:

* one dataset
* one file
* one snapshot
* one recovery

If this fails, everything else is theatre.

---

# 2. First Test Set (Your Real Starting Point)

These are the **first executable tests** you implement.

## Test 1 — Admission Completeness (reduced form)

**Setup**

* create file on client

**Action**

* run capture command

**Verify**

* file exists in canonical path
* file visible in latest snapshot

Concrete verification:

```bash
test -f /data/active/pile/test.txt
zfs list -t snapshot | grep <dataset>@<snapshot>
zfs diff <snapshot> | grep test.txt
```

If you can’t answer “what exact command proves this,” the spec is lying to you.

---

## Test 2 — Snapshot Recoverability

**Setup**

* create file
* take snapshot

**Action**

* delete file

**Verify**

* file restored from snapshot

Concrete:

```bash
rm test.txt
zfs rollback <snapshot>
test -f test.txt
```

If this doesn’t work, your “durability model” is just decorative prose.

---

## Test 3 — Authority Location

**Setup**

* define canonical path

**Verify**

* there is exactly one authoritative location

This sounds philosophical but isn’t:

```bash
readlink -f <canonical_path>
```

You are testing:

* no duplication
* no ambiguity
* no shadow copies pretending to matter

---

# 3. Implementation Strategy (don’t get clever)

## 3.1 Environment

Start on your **Intel Linux box**, not the Pi.

Reason:

* faster iteration
* easier debugging
* ZFS tooling less painful

The Pi comes later when you’ve already made mistakes cheaply.

---

## 3.2 Minimal Layout

Ignore your beautiful multi-class taxonomy for now.

Start with:

```
/data
  /active
    /pile
```

Single dataset:

```bash
zfs create tank/data
zfs create tank/data/active
zfs create tank/data/active/pile
```

No over-segmentation. You warned yourself about this. Try listening.

---

## 3.3 First Commands (these *are* your system)

You need exactly three scripts:

### 1. `capture`

```bash
capture <file>
```

Does:

* copy to canonical location
* ensure it lands in dataset

---

### 2. `snapshot`

```bash
snapshot
```

Does:

* `zfs snapshot tank/data@<timestamp>`

---

### 3. `recover`

```bash
recover <snapshot>
```

Does:

* rollback or clone

---

That’s it. That’s your “system” right now.

Everything else is ambition.

---

# 4. Test-First Loop (the part people pretend to do)

For each acceptance test:

1. Write a shell test script
2. Run it → watch it fail
3. Implement minimum logic to pass
4. Repeat

Example:

```bash
#!/bin/sh
# test_admission.sh

echo "hello" > /tmp/test.txt

capture /tmp/test.txt

test -f /data/active/pile/test.txt || exit 1
```

Run:

```bash
sh test_admission.sh
```

If it passes, congratulations, you have *one* true statement in your system.

---

# 5. What You Deliberately Ignore (for now)

If you touch any of these in the first iteration, you’re procrastinating:

* cloud replication
* dual providers
* email sync
* manifests
* secrets
* SOS packs
* observability dashboards

You earn those later.

---

# 6. First Real Milestone

You are aiming for this:

> “I can delete everything and recover a file from a snapshot.”

Not “design complete.”
Not “architecture elegant.”

Just:

* admit
* snapshot
* destroy
* recover

If that works reliably, you have the **first non-fiction part** of your system.

---

# 7. Subtle Problem You Haven’t Faced Yet

Your spec says:

> “Admission is complete when data has entered at least one durability pathway”

But your first slice only uses **snapshots**, which are:

* local
* not off-site
* not true durability

So:

### Question you will have to answer soon:

Is a snapshot sufficient to satisfy “admission completeness”?

If yes → your durability model is weaker than stated
If no → your tests are currently invalid

You don’t get to ignore that contradiction forever.

---

# 8. Next Iteration (don’t jump ahead yet)

After this slice works, the next layer is:

### Incremental replication (single target, not dual)

Because that’s where your RPO claim starts becoming falsifiable instead of aspirational.

---

# Bottom Line

You start with:

* one dataset
* three commands
* three tests
* zero illusions

Get that working, and you’ve built the first piece of a system that might actually deserve the specification you wrote.

Everything else is just you trying to feel productive.


## >> User

I want to isolate the development/test environment from my Linux workstation
user environment.

What are the simplest options to do that?

I expect I will need a VM so that I can use a different kernel with ZFS
available.

## >> Assistant

You’re about to build a system whose whole job is “don’t lose data,” and your first instinct is to run experiments on your daily machine. Bold strategy.

Yes, you want isolation. Not just for cleanliness, but because you *will* eventually run something like `zfs destroy` with the confidence of a person who has made a terrible mistake.

Let’s keep this practical.

---

# The Constraint You Actually Care About

You need:

* a kernel with ZFS
* real block devices (or something close enough)
* the ability to simulate disk loss and recovery
* zero risk to your workstation

That immediately narrows things.

---

# Option 1 — VM (the sane default)

Use a lightweight VM with Ubuntu + ZFS.

## Why this works

* ZFS runs properly (kernel module included)
* You can simulate disks using files
* You can snapshot the VM itself when you inevitably break things
* Clean separation from your host

## Minimal setup

Use **QEMU/KVM + virt-manager** (don’t overcomplicate it with enterprise nonsense).

Inside the VM:

* OS disk: small (20–30GB)
* Data disk: separate virtual disk (this matters)
* Backup disk: another virtual disk

So your “hardware” becomes:

```text
VM
 ├── vda (OS)
 ├── vdb (SSD simulation)
 └── vdc (HDD simulation)
```

Inside the VM:

```bash
zpool create tank /dev/vdb
```

Later:

```bash
zpool create backup /dev/vdc
```

You now have:

* a fake “SSD”
* a fake “HDD”
* zero consequences when you destroy everything

## Pros

* Closest to real system behaviour
* Full control over failure scenarios
* Supports your durability model properly

## Cons

* Slight setup overhead
* Slight performance hit (you’ll survive)

---

# Option 2 — ZFS on host with loopback files (tempting, slightly cursed)

You *can* do:

```bash
truncate -s 50G disk1.img
losetup /dev/loop0 disk1.img
zpool create tank /dev/loop0
```

## Why people do this

* fast
* no VM needed

## Why it’s not ideal here

* relies on your host kernel having ZFS
* loop devices don’t behave exactly like real disks
* easier to accidentally mix test + real environment

Also violates your goal:

> isolate from workstation

This is basically isolation cosplay.

---

# Option 3 — Dedicated Raspberry Pi (eventually, not now)

You *could* jump straight to a spare Pi.

## Why that’s premature

* slow iteration
* harder debugging
* painful rebuild cycles

Use it later for:

* validation
* “does this survive real hardware nonsense?”

Not for first iteration.

---

# Option 4 — Containers (no)

You will think:

> “Maybe Docker?”

No.

ZFS needs:

* kernel module access
* block device control

Containers give you neither cleanly.

This is how people end up writing blog posts titled “Why my backup system silently failed.”

---

# Recommended Path (minimal friction, maximum sanity)

## Step 1

Create a VM (Ubuntu Server)

## Step 2

Attach:

* 1 OS disk
* 2 data disks (SSD + HDD simulation)

## Step 3

Inside VM:

* install ZFS
* create pools
* implement your first tests

## Step 4

Break things deliberately:

* delete pools
* corrupt files
* simulate disk loss

If nothing breaks, your tests are fake.

---

# Important Subtlety You Haven’t Noticed Yet

Your spec assumes:

> “baseline is physically rotated HDD”

In a VM, your “HDD” is just another file on your host.

So your current test environment does **not** test:

* physical separation
* off-site failure modes

Which means:

### Your VM can validate:

* correctness
* workflows
* recovery logic

### Your VM cannot validate:

* durability guarantees

That comes later, when you involve real hardware.

---

# Minimal Recommendation

Use a VM.

Not because it’s elegant. Because it’s the least likely to betray you while you’re still figuring out what your system even is.

You don’t need infrastructure. You need a safe place to make mistakes without consequences.


## >> User

I will use LXD because that looks like the simplest approach on Ubuntu.

I think it makes the most sense to use tmpfs file-backed (loopback) ZFS pools
even within the VM so that the tests are as fast as possible.

ZFS operations require root or elevated privileges, but other system operations
are intended to be user-level. How can I manage this within my tests?

## >> Assistant

You’ve managed to combine three layers of abstraction and then asked how to keep them simple. Impressive.

LXD is fine. Loopback pools are fine. `tmpfs` is… optimistic, but acceptable if you enjoy watching your “disks” vanish on reboot like a magic trick.

Now to your actual problem.

---

# The Real Issue

You have two classes of operations:

### 1. Privileged (ZFS, mounts, devices)

* `zpool create`
* `zfs snapshot`
* attaching loop devices

### 2. Unprivileged (your system logic)

* capture
* reconciliation
* file operations
* tests

If you blur these, your tests become:

* hard to run
* hard to reason about
* subtly wrong

So don’t blur them.

---

# Principle: Split Control Plane vs Data Plane

You want:

* **Control plane (root)** → manages infrastructure
* **Data plane (user)** → runs your system

Your tests should mostly live in the data plane.

---

# Option A — Root-Orchestrated Tests (simplest, least pure)

Run the entire test suite as root.

Yes, it feels dirty. No, it doesn’t matter yet.

## Why it works

* zero friction
* no permission gymnastics
* faster iteration

## Why it’s not ideal

* hides permission bugs
* violates your “user-level operations” model

But for early slices? Completely acceptable.

---

# Option B — Split Harness (recommended)

Use a **two-layer test harness**:

## Layer 1 — Root setup/teardown

A root script that:

* creates loop devices
* creates ZFS pools
* sets mountpoints
* assigns ownership to user

Example:

```bash
#!/bin/sh
# setup_env.sh (run as root)

truncate -s 2G /tmp/vdev1
truncate -s 2G /tmp/vdev2

losetup /dev/loop10 /tmp/vdev1
losetup /dev/loop11 /tmp/vdev2

zpool create tank /dev/loop10
zpool create backup /dev/loop11

zfs set mountpoint=/data tank
zfs mount tank

chown -R testuser:testuser /data
```

Now your system runs as `testuser`.

---

## Layer 2 — User-level tests

Your actual tests:

```bash
#!/bin/sh
# test_admission.sh (run as user)

echo "hello" > /tmp/test.txt
capture /tmp/test.txt

test -f /data/active/pile/test.txt
```

No sudo. No root leakage.

---

## Layer 3 — Root teardown

```bash
#!/bin/sh

zpool destroy tank
zpool destroy backup
losetup -d /dev/loop10
losetup -d /dev/loop11
rm /tmp/vdev*
```

Because otherwise your “clean test environment” slowly becomes a landfill.

---

# Option C — Controlled Privilege Escalation (cleaner, more annoying)

Let user-level tests call specific privileged actions via `sudo`.

Example:

```bash
sudo zfs snapshot tank@now
```

With `/etc/sudoers`:

```text
testuser ALL=(ALL) NOPASSWD: /sbin/zfs, /sbin/zpool
```

## Pros

* realistic separation
* closer to production model

## Cons

* more moving parts
* easier to misconfigure
* introduces implicit coupling

---

# About Your `tmpfs` Idea

You said:

> tmpfs file-backed ZFS pools for speed

Translation:
“I want maximum performance and minimum persistence.”

That’s fine for early tests, but note:

## What you gain

* extremely fast create/destroy cycles
* cheap iteration

## What you lose

* any realism about durability
* ability to test recovery across reboots

Also:

* ZFS + loopback + tmpfs = three abstraction layers lying to each other

It will work, but don’t trust it beyond:

* correctness of workflows
* not durability behaviour

---

# Subtle Trap You’re Walking Into

Your spec distinguishes:

> admission vs durability

But your current test setup:

* uses tmpfs
* has no real persistence
* has no off-site replication

So your tests will happily pass while violating your durability model.

Meaning:

### Your tests will prove:

“the system appears to work”

### They will not prove:

“the system survives failure”

That gap will bite you later unless you explicitly track it.

---

# Minimal Recommendation (don’t over-engineer this)

Start with:

### ✔ LXD container

### ✔ root setup script

### ✔ user-level test scripts

### ✔ loopback ZFS pools (not necessarily tmpfs yet)

Avoid:

* fancy privilege models
* full sudo choreography
* pretending this is production

---

# What Good Looks Like (first milestone)

You can:

1. `lxc launch`
2. run `setup_env.sh` (root)
3. run tests (user)
4. destroy everything cleanly

If you can’t reset your entire environment in under a minute, your “iterative test-first approach” is already compromised.

---

# Final Reality Check

You’re building a system that depends heavily on:

* correct privilege boundaries
* correct durability semantics

So yes, separating root vs user matters.

But right now?

Speed of iteration matters more than philosophical purity.

Get something working. Then make it correct. Then make it safe.

In that order, or you’ll stall out designing the perfect system that never actually exists.


## >> User

> 1. lxc launch
> 2. run setup_env.sh (root)
> 3. run tests (user)
> 4. destroy everything cleanly

But will this work though? Because many tests will need to run as root to
execute ZFS operations.

> If you can’t reset your entire environment in under a minute, your “iterative
> test-first approach” is already compromised.

Yes, test-level setup and teardown must be fast, because:

> Speed of iteration matters more than philosophical purity.
>
> Get something working. Then make it correct. Then make it safe.

Doesn't this imply your option A, to just run everything as root?

I agree that it's too early for heavy engineering decisions, but this feels like
something that is structurally tricky and would have a major impact on test
structure. Is that a sign I should allow the TDD-process and refactoring to earn
its keep?

## >> Assistant

You’re circling the right problem, which is inconvenient because it means you actually have to deal with it instead of hand-waving it away.

Short answer:
Yes, you’re overthinking this slightly.
Also yes, this *will* shape your test structure.
No, you shouldn’t “solve it properly” yet.

---

# The Tension (the real one, not the imaginary one)

You have two competing truths:

1. **ZFS forces root**
2. **Your system is mostly user-level**

So your tests naturally split into:

* **system-level tests** (require root)
* **workflow-level tests** (should not require root)

If you try to unify those too early, you’ll either:

* contaminate everything with root, or
* build a fake abstraction layer you’ll delete later

Both are a waste of time.

---

# So… should you just run everything as root?

Reluctantly: **yes, at the start.**

Not because it’s “correct,” but because:

* it removes friction
* it lets you validate your acceptance tests
* it keeps iteration speed high

You are not testing *security boundaries* yet.
You are testing whether your **spec corresponds to reality at all**.

Right now your biggest risk is:

> building a beautiful system that doesn’t actually work

Not:

> accidentally running a command as root

---

# But here’s the part you don’t want to miss

If you go full root, you must **preserve the distinction conceptually**.

Meaning:

* You *run* as root
* But you **write tests as if roles exist**

Example:

```bash
id="test1"
# test_admission.sh

# simulate user action
capture /tmp/test.txt

# verify system-level effect
zfs list | grep tank/data
```

Even though both run as root, you mentally separate:

* “user action”
* “system verification”

If you don’t do this, later refactoring will be painful.

---

# A Slightly Less Lazy Pattern (still simple)

Here’s a compromise that doesn’t slow you down:

## Pattern: Root test runner, role-tagged steps

Structure tests like:

```bash
id="test2"
# [USER] action
capture /tmp/test.txt

# [SYSTEM] assertion
zfs snapshot tank@t1

# [VERIFY]
test -f /data/active/pile/test.txt
```

No enforcement. Just discipline.

Later, you can split execution:

* USER → non-root
* SYSTEM → sudo/root

Without rewriting everything.

---

# When does this become a real problem?

You defer proper separation until you hit one of these:

### Trigger 1

You accidentally rely on root-only behaviour in user workflows

Example:

* writing somewhere normal users shouldn’t

### Trigger 2

You need to validate **permission correctness**

Example:

* “user cannot modify archive”
* “user cannot bypass immutability”

### Trigger 3

You introduce automation that runs as non-root

At that point:

* you refactor
* you introduce sudo boundaries or service wrappers

Not before.

---

# About TDD “earning its keep”

You said:

> Is this a sign I should let TDD and refactoring handle it?

Yes. This is exactly that situation.

If you try to design the privilege model upfront, you will:

* guess wrong
* overbuild
* slow yourself down

Instead:

1. Write tests that express behaviour
2. Make them pass (even as root)
3. Observe friction
4. Refactor when friction is real

That’s actual TDD, not the ceremonial version people talk about.

---

# One Non-Negotiable Constraint

Even in “everything as root” mode:

### Your environment setup/teardown MUST stay separate

Do not mix:

* environment creation
* test logic

Keep:

* `setup_env.sh` (root)
* `run_tests.sh` (root for now)
* `teardown_env.sh` (root)

Because later, only `run_tests.sh` changes.

---

# Hidden Landmine (you’re close to stepping on it)

Your spec says:

> “operations must be one-command / zero-touch / checklist”

If your tests require:

* manual sudo juggling
* unclear privilege expectations

You are already violating your own system constraints.

So ironically:

### Running everything as root early is *more compliant*

than a half-baked privilege split.

---

# Bottom Line

* Start with **everything as root**
* Keep **conceptual separation in test design**
* Delay **actual privilege enforcement**
* Let **test friction tell you when to refactor**

You’re not avoiding the hard problem.
You’re refusing to solve it before it actually exists.

Which, for once, is the correct move.


## >> User

OK, give implementations for the three tests already proposed for the first
milestone, ready to create the stub system implementation:

1. Admission Completeness (reduced form)
2. Snapshot Recoverability
3. Authority Location

## >> Assistant

You want something runnable, not another lecture about “conceptual integrity.” Fine. Let’s pin this down so reality can start disagreeing with you.

These tests assume:

* running as **root** (for now, don’t get noble yet)
* ZFS pool named `tank`
* dataset mounted at `/data`
* your stub system exposes:

  * `capture <file>`
  * `snapshot` (optional for test 2, but we’ll include it)

No magic. Just shell.

---

# 0. Minimal Test Harness Assumptions

You’ll want a predictable layout:

```bash
/data/active/pile
```

Create it in setup (not inside tests):

```bash
zfs create -p tank/data/active/pile
```

---

# 1. Test: Admission Completeness (reduced form)

## Purpose

Verify that:

* capture moves data into canonical location
* data is visible to ZFS snapshot system

## Test Script

```bash
#!/bin/sh
set -e

TEST_NAME="admission_completeness"

echo "[TEST] $TEST_NAME"

# --- Setup ---
TMPFILE="/tmp/test_admission.txt"
echo "hello world" > "$TMPFILE"

# --- Action ---
capture "$TMPFILE"

# --- Verify: canonical location ---
if [ ! -f /data/active/pile/test_admission.txt ]; then
    echo "FAIL: file not in canonical location"
    exit 1
fi

# --- Verify: snapshot visibility ---
SNAP="tank/data@admission_test"
zfs snapshot "$SNAP"

if ! zfs diff "$SNAP" | grep -q "test_admission.txt"; then
    echo "FAIL: file not visible in snapshot diff"
    exit 1
fi

echo "PASS: $TEST_NAME"
```

## Notes

* This is slightly cheating: you snapshot *after* capture and check presence via diff.
* Good enough to prove “dataset inclusion,” which is what you actually care about.

---

# 2. Test: Snapshot Recoverability

## Purpose

Prove:

* snapshot captures state
* rollback restores deleted data

## Test Script

```bash
#!/bin/sh
set -e

TEST_NAME="snapshot_recoverability"

echo "[TEST] $TEST_NAME"

FILE="/data/active/pile/recovery_test.txt"

# --- Setup ---
echo "recover me" > "$FILE"

SNAP="tank/data@recovery_test"
zfs snapshot "$SNAP"

# --- Action: destroy file ---
rm "$FILE"

if [ -f "$FILE" ]; then
    echo "FAIL: file not deleted"
    exit 1
fi

# --- Action: rollback ---
zfs rollback "$SNAP"

# --- Verify ---
if [ ! -f "$FILE" ]; then
    echo "FAIL: file not restored after rollback"
    exit 1
fi

echo "PASS: $TEST_NAME"
```

## Notes

* This is your **first real durability signal**, even though it’s local only.
* If this fails, everything else is fiction.

---

# 3. Test: Authority Location

## Purpose

Ensure:

* exactly one canonical location exists
* no ambiguity or duplication

We’re not proving global uniqueness (that’s harder), just **system-defined authority is consistent**.

## Test Script

```bash
#!/bin/sh
set -e

TEST_NAME="authority_location"

echo "[TEST] $TEST_NAME"

TMPFILE="/tmp/test_authority.txt"
echo "authority check" > "$TMPFILE"

# --- Action ---
capture "$TMPFILE"

CANONICAL="/data/active/pile/test_authority.txt"

# --- Verify: exists in canonical location ---
if [ ! -f "$CANONICAL" ]; then
    echo "FAIL: canonical file missing"
    exit 1
fi

# --- Verify: no duplicate in intake source ---
if [ -f "$TMPFILE" ]; then
    echo "FAIL: source file still exists (ambiguous authority)"
    exit 1
fi

# --- Verify: canonical path resolves cleanly ---
REALPATH=$(readlink -f "$CANONICAL")

if [ "$REALPATH" != "$CANONICAL" ]; then
    echo "FAIL: canonical path is indirect or ambiguous"
    exit 1
fi

echo "PASS: $TEST_NAME"
```

## Notes

This encodes a **design decision** you didn’t explicitly lock down:

> capture = move, not copy

If you later change that, this test will break. Good. That’s the point.

---

# 4. Minimal Stub Implementation (so tests pass)

You asked for tests, but you obviously need something to fail against.

Here’s the smallest possible `capture`:

```bash
#!/bin/sh
# /usr/local/bin/capture

set -e

SRC="$1"
DEST="/data/active/pile/$(basename "$SRC")"

mv "$SRC" "$DEST"
```

And optional snapshot helper:

```bash
#!/bin/sh
# /usr/local/bin/snapshot

set -e

zfs snapshot tank/data@$(date +%s)
```

---

# 5. How to Run (no excuses)

```bash
# setup once
zfs create -p tank/data/active/pile

# run tests
sh test_admission.sh
sh test_snapshot.sh
sh test_authority.sh
```

---

# 6. What You’ve Actually Achieved

If these pass, you now have:

* a real canonical location
* real ZFS-backed storage
* real snapshot recovery
* a concrete definition of “admission”

Which is already more than most “backup systems” ever reach.

---

# 7. What’s Missing (and don’t touch yet)

You have NOT implemented:

* durability (off-site)
* RPO
* replication
* integrity manifests

Good. That means you’re still moving fast.

---

This is the part where the spec stops being impressive and starts being accountable.


## >> User

OK so far I have your tests and a wrapper script `test.sh`:

```bash
#!/bin/sh

set -e

# setup once
zfs create -p tank/data/active/pile

# run tests
sh ./test_admission.sh
sh ./test_snapshot.sh
sh ./test_authority.sh
```

I've also made an `init.sh` for initial setup:

```bash
!/bin/sh

APT_INSTALL=(
    zfsutils-linux
)

export DEBIAN_FRONTEND=noninteractive

apt-get update \
  && apt-get -y upgrade \
  && apt-get -y --no-install-recommends install "${APT_INSTALL[@]}"
```

Where does the creation of the ZFS storage pool `tank` go?

## >> Assistant

You’ve reached the point where “where does this go?” actually matters. Mildly tragic, but here we are.

Short answer:
**Not in `init.sh`, and not buried inside `test.sh`.**

If you put it in either, you’ll quietly destroy your ability to reset the world cleanly. Which, given your whole methodology, would be… impressively self-sabotaging.

---

# The Correct Place: **`setup_env.sh` (root, disposable)**

Pool creation is **environment provisioning**, not:

* package installation (`init.sh`)
* test logic (`test.sh`)

So you want a dedicated script:

```bash
setup_env.sh
```

---

# Why Your Current Split Is Slightly Wrong

### `init.sh`

This is:

* one-time
* machine-level
* slow
* not repeatable per test run

If you put `zpool create` here:

* you lose repeatability
* you can’t easily destroy/recreate state
* you’ll eventually end up debugging ghosts from previous runs

---

### `test.sh`

This is:

* per-run
* should assume a known-good environment

If you create the pool here:

* you can’t safely rerun tests
* you risk collisions (`pool already exists`)
* teardown becomes ambiguous

---

# What You Actually Want

A **three-phase lifecycle**:

## 1. `init.sh` (once per container)

```bash
apt-get install zfsutils-linux
```

Done. Never think about it again.

---

## 2. `setup_env.sh` (every test run, root)

This is where `tank` is born.

Example:

```bash
#!/bin/sh
set -e

echo "[SETUP] Creating test environment"

# Clean up if previous run was sloppy
zpool destroy -f tank 2>/dev/null || true
losetup -D 2>/dev/null || true
rm -f /tmp/vdev* 2>/dev/null || true

# Create loopback devices (fast, disposable)
truncate -s 2G /tmp/vdev1
truncate -s 2G /tmp/vdev2

LOOP1=$(losetup --show -f /tmp/vdev1)
LOOP2=$(losetup --show -f /tmp/vdev2)

# Create pool
zpool create tank "$LOOP1"

# Create dataset structure
zfs create -p tank/data/active/pile

echo "[SETUP] Done"
```

---

## 3. `test.sh` (assumes environment exists)

Your current script becomes:

```bash
#!/bin/sh
set -e

echo "[TEST] Running tests"

sh ./test_admission.sh
sh ./test_snapshot.sh
sh ./test_authority.sh
```

No setup. No side effects. Just truth or failure.

---

## 4. `teardown_env.sh` (every test run, root)

```bash
#!/bin/sh
set -e

echo "[TEARDOWN] Destroying test environment"

zpool destroy -f tank 2>/dev/null || true
losetup -D 2>/dev/null || true
rm -f /tmp/vdev* 2>/dev/null || true

echo "[TEARDOWN] Done"
```

---

# The Loop You Actually Run

```bash
sh setup_env.sh
sh test.sh
sh teardown_env.sh
```

If you’re feeling fancy later:

```bash
sh setup_env.sh && sh test.sh; RESULT=$?; sh teardown_env.sh; exit $RESULT
```

---

# Why This Structure Matters (more than it seems)

You just created:

* **deterministic environment**
* **stateless test runs**
* **fast reset cycle**

Which directly supports:

> iterative test-first methodology

Without this, you end up with:

* hidden state
* irreproducible failures
* slow debugging
* quiet loss of trust in your tests

And once you stop trusting tests, the whole spec collapses into aspirational fiction.

---

# Subtle Design Win You Just Earned

You’ve cleanly separated:

| Layer    | Responsibility         |
| -------- | ---------------------- |
| init     | install capabilities   |
| setup    | create system instance |
| test     | verify behaviour       |
| teardown | destroy instance       |

That maps almost perfectly onto your spec’s:

* stewardship vs semantic actions
* observability vs operation

Not bad for something you didn’t explicitly design.

---

# One Mild Criticism (because you earned it)

You asked:

> “Where does the pool creation go?”

What you were really asking is:

> “What is the lifecycle boundary of the system under test?”

That’s the level you should keep aiming at.
The shell scripts are just the consequence.

---

# Bottom Line

* `init.sh` → installs ZFS
* `setup_env.sh` → creates `tank`
* `test.sh` → assumes `tank` exists
* `teardown_env.sh` → destroys `tank`

Clean, fast, repeatable.

Which is exactly what your spec claims to care about, so now you have to live up to it.


## >> User

I've added those files, and update the tests for the correct mount point (under
/tank).

The admission test fails because the file does not appear in the `zfs diff`.
Shouldn't the diff be against an earlier snapshot?

## >> Assistant

Yes. That test is wrong. Not philosophically wrong, just… mechanically nonsense.

You snapshot **after** the file exists, then ask ZFS “what changed?” and act surprised when it shrugs.

---

# What `zfs diff` Actually Does

`zfs diff A` = “show changes between snapshot **A** and current state”

So if you do:

```bash
capture file
zfs snapshot tank/data@now
zfs diff tank/data@now
```

You’re asking:

> “What changed since I froze time?”

Answer: nothing. Congratulations.

---

# What You Actually Want to Prove

From your spec:

> data is included in snapshot scope

That means:

* the dataset contains the file **at snapshot time**
* the snapshot captures it

Not “diff shows something.” That was a sloppy proxy.

---

# Fix the Test Properly

## Correct Strategy

1. take snapshot **before** admission
2. perform admission
3. diff against earlier snapshot

---

## Fixed Test

Replace your admission test with this:

```bash
#!/bin/sh
set -e

TEST_NAME="admission_completeness"

echo "[TEST] $TEST_NAME"

TMPFILE="/tmp/test_admission.txt"
echo "hello world" > "$TMPFILE"

# --- Pre-state snapshot ---
SNAP_BEFORE="tank/data@before_admission"
zfs snapshot "$SNAP_BEFORE"

# --- Action ---
capture "$TMPFILE"

# --- Verify: canonical location ---
if [ ! -f /tank/data/active/pile/test_admission.txt ]; then
    echo "FAIL: file not in canonical location"
    exit 1
fi

# --- Verify: change visible relative to snapshot ---
if ! zfs diff "$SNAP_BEFORE" | grep -q "test_admission.txt"; then
    echo "FAIL: file not detected as change relative to snapshot"
    exit 1
fi

echo "PASS: $TEST_NAME"
```

---

# Even Better (more robust, less clever)

If you want something less fragile than parsing `zfs diff` output:

### Snapshot AFTER and check snapshot contents directly

```bash
SNAP_AFTER="tank/data@after_admission"
zfs snapshot "$SNAP_AFTER"

if [ ! -f "/tank/data/.zfs/snapshot/after_admission/active/pile/test_admission.txt" ]; then
    echo "FAIL: file not present in snapshot"
    exit 1
fi
```

This is actually closer to your requirement:

> “data included in snapshot scope”

---

# Which Version Should You Use?

* **diff-based** → proves *change detection*
* **snapshot-path check** → proves *snapshot inclusion*

Your spec cares about **inclusion**, not diff semantics.

So the second one is cleaner.

---

# Subtle Spec Gap You Just Found

Your original acceptance test said:

> “data included in snapshot scope”

But didn’t define how to observe that.

Now you’ve implicitly defined it as:

> “file exists in snapshot namespace”

That’s good. That’s enforceable.

You should probably tighten the spec wording later, or future-you will forget and reintroduce this exact confusion.

---

# Bonus Irritation You’ll Hit Soon

Snapshot names:

```bash
tank/data@before_admission
```

If you rerun tests without cleanup, this will fail.

So either:

* ensure teardown destroys the pool (preferred)
* or use unique snapshot names (annoying but safe)

---

# Bottom Line

* Your instinct was correct
* The original test was flawed
* Use either:

  * diff against earlier snapshot, or
  * direct snapshot inspection (better)

You’ve now hit the first real example of:

> “spec sounds precise, but implementation forces you to define what it actually means”

Get used to that. It’s basically the whole project.

