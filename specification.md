<!-- vim: set filetype=markdown: -->

# Personal Information Management System Specification

## Draft v0.2

---

## 1. Introduction

### 1.1 Purpose

This specification defines a personal information management system intended to govern how information is admitted, organised, protected, retained, and recovered across a heterogeneous personal information estate.

The system exists to ensure that information of ongoing personal, operational, or historical significance remains:

* locatable,
* interpretable,
* recoverable,
* maintainable over long time horizons,
* governable under realistic resource constraints.

The specification addresses not only storage arrangement but also authority, lifecycle, and protection responsibility.

It distinguishes between:

* information for which the system accepts explicit custody obligation,
* information temporarily outside canonical authority during ordinary work,
* information whose long-term classification remains unresolved.

The intent is durable coherence rather than maximal formalism.

---

### 1.2 Scope

This specification governs information for which the system accepts ongoing custody responsibility, together with the operational mechanisms required to preserve interpretability and recoverability.

Included material comprises:

* personal retained records,
* mutable operational repositories,
* service-backed communications,
* active project material,
* static collected material,
* integrity and recovery artefacts,
* controlled peripheral capture pending reconciliation or disposition.

Excluded are:

* disposable transient artefacts,
* incidental device-local residue,
* replaceable material not admitted into governed classes.

The specification defines principles and class behaviour rather than exhaustive tooling implementation unless tooling materially affects authority, mutation, or recoverability.

---

### 1.3 Operator Domains

The system distinguishes between two categories of operator action because they impose different risks, review burdens, and control requirements.

#### Stewardship Actions

Stewardship actions maintain continuity, integrity, and recoverability of the information estate without materially changing informational meaning.

Examples include:

* backup rotation,
* snapshot verification,
* manifest maintenance,
* recovery source refresh,
* integrity checking,
* service health verification.

Failure in stewardship actions may leave ordinary use apparently unaffected while degrading long-term recoverability or interpretability.

These actions favour explicit procedure, repeatability, and bounded omission risk.

#### Semantic Actions

Semantic actions alter the meaning, classification, placement, or interpretive usefulness of information within the system.

Examples include:

* file review,
* classification,
* renaming,
* note editing,
* project restructuring,
* archival decisions.

Failure in semantic actions primarily degrades interpretability, discoverability, or long-term informational coherence.

These actions require flexible judgement rather than rigid procedural repetition.

---

### 1.4. Guiding Principles

#### Canonical Custody Principle

The system shall maintain clearly identifiable canonical authority for governed information.

For each canonical class:

* an authoritative location shall be identifiable,
* protection obligations shall be explicit,
* restoration paths shall be definable.

Canonical status is a custody property, not a judgement of intrinsic value or completeness.

#### Late Commitment Principle

The system shall avoid premature irreversible classification where later understanding may materially alter value, destination, or interpretation.

Accordingly:

* newly admitted material may enter governed intake before full classification,
* provisional content may remain protected while unresolved,
* final placement may be deferred where immediate certainty is unnecessary.

Protection may precede final judgement.

#### Resource-Constrained Durability Principle

Durability obligations shall reflect realistic limits of storage, bandwidth, operational effort, and review capacity.

The system shall therefore apply stronger guarantees where replacement cost, interpretive value, or operational dependence justify them, while permitting bounded asymmetry where universal maximal redundancy would impose disproportionate burden.

Durability is governed, not idealised.

#### Separation of Mutation Regimes

Information classes with materially different mutation behaviour shall remain structurally distinct where that distinction affects authority, retention, integrity handling, or recovery design.

In particular, the system distinguishes between:

* mutable repositories,
* append-dominant streams,
* service-mediated streams,
* static retained corpora,
* controlled intake stages.

This prevents one class from inheriting unsuitable operational assumptions from another.

#### Controlled Transience Principle

Temporary divergence from canonical authority is permitted where operationally necessary, provided such divergence remains bounded and routinely reconciled.

This applies particularly to:

* active client-side editing,
* local capture,
* recent mutable work awaiting reconciliation.

Transient operational state shall not become undeclared alternate authority.

---

## 2. Definitions

### 2.1 Canonical

Information is **canonical** when it belongs to a governed class for which the system explicitly accepts preservation, integrity, and recovery responsibility.

Canonical status requires:

* governed class membership,
* identifiable protection path,
* recoverable authoritative form.

Canonical status does not imply immutability.

Canonical information may be highly mutable.

#### Canonical Authority

**Canonical authority** identifies the location currently recognised as authoritative for a canonical item or dataset.

In normal operation:

* canonical authority resides server-side,
* authoritative history is server-reconciled,
* client copies are derivative except during transient authoritative state.

Canonical authority defines conflict resolution and authoritative history, not durability status.

In cases of ambiguity, canonical authority defaults to the last successfully reconciled server-side state unless explicitly superseded by a defined recovery procedure.

#### Canonical Class

A **canonical class** is a governed category of information whose members share authority expectations, mutation characteristics, lifecycle assumptions, and protection obligations.

---

### 2.2 Provisional

Information is **provisional** when its long-term classification, final destination, retention significance, or stable form remains unresolved.

Provisional content may still be canonical if already admitted to a governed class.

Provisional designation does not imply low value or reduced protection.

---

### 2.3 Transient Authoritative State

**Transient authoritative state** exists when current working information temporarily resides outside canonical authority before reconciliation into its governed canonical class.

Typical examples include:

* unsynchronised client edits,
* recent locally created project work,
* local mutable work awaiting commit and push.

Transient authoritative state is tolerated operationally but is temporary by design.

It does not establish alternate canonical authority.

Transient authoritative state is not covered by durability guarantees unless explicitly captured into a protected dataset.

---

### 2.4 Provenance

**Provenance** describes how information enters the system.

Typical provenance categories include:

* locally originated,
* remotely originated,
* externally collected,
* opportunistically captured.

Authorship origin and ingress pathway may differ.

A locally authored item may operationally arrive through remote synchronisation and still remain locally governed after reconciliation.

### 2.5 Durability state

**Durability state** describes the extent to which information is protected against loss through replication, integrity mechanisms, and recovery capability.

Durability state is independent of canonical authority.

Information may be authoritative but not yet durable, or durable but not authoritative.

---

## 3. Information Model

### 3.1 Model Function

The information model defines the canonical classes through which governed information is admitted, maintained, interpreted, and protected.

Each canonical entity class is characterised by:

* provenance,
* canonical authority,
* mutation profile,
* lifecycle expectation,
* protection obligation.

Classes are distinguished primarily by operational role and only secondarily by storage form or tooling.

The model therefore separates information that may appear technically similar where its authority, retention logic, or interpretive role differs materially.

---

### 3.2 Canonical Entity Classes

The system recognises five top-level canonical entity classes:

* administrative information,
* project work,
* synchronised communication streams,
* static personal material,
* provisional peripheral capture.

These classes collectively define the governed information estate.

---

### 3.3 Administrative Information

Administrative information is system self-description and operational control material required to interpret, maintain, protect, or recover the broader information estate.

Its defining characteristic is that its primary purpose is internal system continuity rather than substantive external output.

This class remains distinct from project work even where tooling and mutation behaviour are similar.

#### 3.3.1 Provenance

Predominantly locally originated.

External fragments may be incorporated where required for operational reference or recovery.

#### 3.3.2 Canonical Authority

Canonical authority resides in server-governed repositories or equivalent governed stores.

Client copies are operational derivatives except during transient authoritative state.

Repository reconciliation restores canonical authority.

#### 3.3.3 Mutation Profile

Generally mutable.

Mutation may be:

* frequent and append-oriented,
* incremental and revisionary,
* occasional structural refactoring.

Subclasses vary significantly in mutation rate.

#### 3.3.4 Lifecycle Expectation

Normally retained indefinitely unless explicitly superseded, consolidated, or retired.

Historical continuity is often operationally valuable.

#### 3.3.5 Protection Obligation

High protection priority.

Loss may impair interpretation, maintenance, or recovery of multiple other classes.

#### 3.3.6 Subclasses

##### Jots

Rapid local capture of short observations, reminders, fragments, or incomplete thoughts.

Typically append-dominant.

Minor short-term correction is normal, but entries generally stabilise quickly.

##### Knowledge Base

Structured retained operational knowledge intended for later reference.

Lower mutation frequency than jots.

Subject to occasional review to prevent silent conceptual drift or obsolescence.

##### Secrets

Sensitive credentials, keys, and confidential operational records.

Canonical custody requires protected representation.

Operational replicas may exist where necessary but remain subordinate to canonical encrypted authority.

##### Tooling

Scripts, templates, configuration material, and operational helper logic used to maintain or operate the information estate.

Multi-device editing is common.

##### SOS Sources

Recovery-oriented source material required to reconstruct, interpret, or restore system state under degraded conditions.

Typically low mutation after establishment.

##### Manifest and Control Artefacts

Integrity metadata and related control structures governing static corpora and recovery interpretation.

Closely coupled to static personal material while remaining administratively distinct because they describe rather than constitute retained content.

---

### 3.4 Project Work

Project work comprises mutable material whose primary purpose is active creation, transformation, analysis, or development directed toward substantive outputs external to system administration.

Its defining characteristic is productive work rather than system self-description.

Outputs may later stabilise into static retained material.

#### 3.4.1 Provenance

Predominantly locally originated.

May incorporate external source material, references, or imported components.

#### 3.4.2 Canonical Authority

Canonical authority normally resides in server-governed repositories.

Multiple client working copies are expected.

Transient authoritative state during active work is normal.

Repository reconciliation restores declared authority.

#### 3.4.3 Mutation Profile

Potentially high mutation.

Patterns include:

* incremental editing,
* restructuring,
* branch divergence,
* burst activity,
* dormant intervals.

#### 3.4.4 Lifecycle Expectation

Finite but variable.

A project may:

* complete and archive,
* promote outputs into static retained classes,
* remain dormant,
* be abandoned deliberately.

Unresolved persistence should remain visible rather than accidental.

#### 3.4.5 Protection Obligation

High during active periods.

Protection asymmetry may be tolerated temporarily where working volume exceeds immediate replication practicality, provided canonical reconciliation remains regular.

The system may include a protected transient project state within project datasets, in which unreconciled working changes are captured and included in incremental replication. This state provides durability protection but does not constitute canonical reconciliation or authoritative history.

---

### 3.5 Synchronised Communication Streams

Synchronised communication streams are canonical records whose operational behaviour depends partly on external service protocols while local custody remains authoritative.

This class includes:

* email,
* contacts,
* calendars.

The defining characteristic is service-mediated synchronisation combined with local retention responsibility.

#### 3.5.1 Provenance

Mixed provenance.

Includes:

* locally authored items,
* remotely received items,
* provider-mediated updates.

Authorship origin and ingress path may differ.

#### 3.5.2 Canonical Authority

Canonical custody remains locally governed even where operational transport occurs through external providers.

Service state may temporarily exceed local active copies without displacing local authority.

#### 3.5.3 Mutation Profile

Predominantly append-dominant.

Historical entries stabilise quickly, though bounded correction remains possible.

#### 3.5.4 Lifecycle Expectation

Recent operational accessibility and long-term retention coexist.

Provider retention may temporarily support operational continuity but does not replace governed preservation.

#### 3.5.5 Protection Obligation

High continuity requirement.

Loss affects historical trace, reference continuity, and operational context.

The system shall aim to preserve full-fidelity local representations of service-backed data where feasible.

---

### 3.6 Static Personal Material

Static personal material comprises substantively stable retained files whose value lies primarily in preservation rather than continued active revision.

This includes:

* personal records,
* received documents,
* collected references,
* stable outputs,
* retained media.

The defining characteristic is long-term retention under low expected mutation.

#### 3.6.1 Provenance

Mixed provenance.

Includes:

* locally generated outputs,
* externally received files,
* externally collected retained material.

#### 3.6.2 Canonical Authority

Canonical authority resides in governed server-side holdings.

Integrity is interpreted through associated manifest and control artefacts.

#### 3.6.3 Mutation Profile

Mutation is lifecycle-dependent.

##### Pile

A governed intake stage permitting:

* additions,
* renaming,
* metadata correction,
* occasional deletion,
* deferred classification.

Pile remains canonical despite unresolved final placement.

##### Filing

After placement, mutation becomes low and deliberate.

##### Collections

Collections are effectively stable after formation.

Subsequent mutation is rare and usually administrative.

#### 3.6.4 Lifecycle Expectation

Long-term retention, usually indefinite.

Pile functions as controlled deferred commitment prior to stable placement.

#### 3.6.5 Protection Obligation

Strong durability requirement.

Integrity verification is central because replacement may be costly, impossible, or historically undesirable.

---

### 3.7 Provisional Peripheral Capture

Provisional peripheral capture comprises material temporarily acquired outside ordinary canonical workflows but retained pending extraction, reconciliation, promotion, or disposal.

Its defining characteristic is bounded uncertainty of destination.

This class exists to prevent accidental loss during deferred judgement.

#### 3.7.1 Provenance

Opportunistic and heterogeneous.

Often client-local, externally captured, or transiently accumulated.

#### 3.7.2 Canonical Authority

Canonical authority is limited and conditional.

Capture may temporarily possess bounded authoritative significance until resolved.

Promotion into another canonical class transfers full canonical authority.

#### 3.7.3 Mutation Profile

Minimal expected mutation beyond:

* extraction,
* triage,
* naming,
* transfer,
* disposal.

#### 3.7.4 Lifecycle Expectation

Short residence preferred.

Persistent accumulation indicates unresolved semantic debt.

#### 3.7.5 Protection Obligation

Limited but non-zero.

Protection should reduce accidental loss during short residence without imposing full long-term preservation burden.

---

## 4. Durability Model

### 4.1 Overview

The system achieves durability through a combination of:

* periodic off-site replication,
* local structural protections,
* incremental off-site buffering of recent changes,
* limited opportunistic capture of non-governed data.

Durability is therefore not uniform across all time horizons.

Instead, it is composed of:

* a **stable baseline** representing the last off-site replication point,
* a **bounded recent-change window** protected by incremental replication,
* **local reversibility mechanisms** protecting against destructive operations.

---

### 4.2 Failure Model

The system is designed to tolerate the following failure classes:

* loss of client device,
* loss of primary server storage,
* partial or total media failure,
* silent data corruption,
* operator error (deletion, overwrite, misclassification),
* loss or unavailability of external services.

Durability mechanisms are evaluated against these failure modes.

---

### 4.3 Baseline Durability

Durability is anchored by periodic replication of canonical datasets to removable off-site storage.

This baseline:

* is considered authoritative for recovery to the most recent rotation point,
* must contain all canonical datasets required for system reconstruction,
* is independent of cloud or service availability.

Recovery to this baseline shall be possible using only:

* the most recent off-site replica,
* recovery-oriented administrative information (SOS pack).

This baseline does not include changes made after the most recent rotation.

---

### 4.4 Recent Change Durability

Changes made after the most recent off-site replication are protected by incremental off-site replication.

This layer:

* captures deltas relative to the last baseline,
* is bounded in size and duration,
* is reset upon subsequent off-site rotation.

The incremental layer shall be replicated to more than one independent remote provider where practicable, such that loss of a single provider does not eliminate recent-change recoverability.

Recovery beyond the baseline requires successful reconstruction of these deltas.

---

### 4.5 Local Reversibility

Within the primary system, destructive operations are mitigated by structural mechanisms including:

* version-controlled repositories,
* filesystem snapshotting,
* append-dominant storage patterns.

These mechanisms provide:

* recovery from accidental deletion or overwrite,
* reconstruction of recent historical states,
* protection against localised corruption.

Local reversibility does not replace off-site durability.

---

### 4.6 Integrity Assurance

Data integrity is ensured through:

* filesystem-level checksumming,
* version control object integrity,
* explicit checksum manifests for static retained material.

Integrity mechanisms must allow detection of:

* silent corruption,
* incomplete replication,
* unintended modification.

---

### 4.7 Service Dependence

Certain classes (e.g. communication streams) rely operationally on external services.

However:

* external services are not considered authoritative for long-term durability,
* local retained copies are required for independent recovery,
* service availability may temporarily mask local gaps but does not satisfy durability obligations.

---

### 4.8 Peripheral Capture

Peripheral capture provides limited short-term protection for non-canonical or not-yet-integrated data.

This mechanism:

* reduces accidental loss,
* does not guarantee durability,
* does not substitute for admission into canonical classes.

Extended reliance on peripheral capture is considered a failure of workflow discipline.

Peripheral and transient data may not be covered by full integrity guarantees; integrity assurance is established only upon admission into canonical classes or protected datasets.

---

### 4.9 Durability Boundaries

The system explicitly accepts:

* recovery to the most recent off-site baseline in the absence of cloud deltas,
* potential loss of recent changes within the bounded incremental replication window,
* temporary exposure during transient authoritative state,
* incomplete protection of non-canonical material.

Full recovery to the most recent state requires:

* a valid off-site baseline, and
* intact incremental replication data.

Loss of both baseline and incremental data constitutes total data loss.

---

## 5. Functional Requirements

### 5.1 Canonical Custody

#### 5.1.1 Canonical Admission

* The system **shall provide a mechanism** to admit information into a canonical class.
* Admission **shall establish canonical authority** and associated protection obligations.
* Information **shall not be considered protected** until admitted into a canonical class.
* Admission establishes a protection obligation but does not guarantee immediate durability; durability is achieved only once the data has entered replication and integrity workflows.
* Admission is considered complete when data is present in canonical authority and has entered at least one defined durability pathway (e.g. snapshot or replication).

---

#### 5.1.2 Canonical Authority Enforcement

* Each canonical item or dataset **shall have a single identifiable canonical authority**.
* The system **shall prevent ambiguity** regarding authoritative location.
* Derivative copies **shall not silently assume canonical authority**.

---

#### 5.1.3 Reconciliation of Transient State

* The system **shall provide mechanisms** to reconcile transient authoritative state into canonical classes.
* Reconciliation **shall be explicit or automatable**.
* The system **shall not rely on indefinite persistence** of transient authoritative state.

---

### 5.2 Capture and Ingestion

#### 5.2.1 Low-Friction Capture

* The system **shall support capture of new information requiring minimal prior classification or decision-making**.

---

#### 5.2.2 Controlled Intake (Pile)

* The system **shall provide a governed intake area** for static material pending classification.
* Material in this area:

  * **shall be canonical**,
  * **shall be protected according to canonical obligations**,
  * **may remain unclassified for a bounded period**.

The system shall provide visibility into the age distribution of items within controlled intake (pile), including identification of items exceeding defined provisional retention bounds.

---

#### 5.2.3 Peripheral Capture

* The system **may support opportunistic capture** of non-canonical data from client devices.
* Such data:

  * **shall be explicitly non-canonical**,
  * **shall not be assumed durable**,
  * **shall be eligible for promotion or discard**.

---

### 5.3 Mutation and Versioning

#### 5.3.1 Mutable Repositories

* The system **shall support versioned mutation** for classes with ongoing modification.
* Version history **shall enable recovery from destructive updates**.

---

#### 5.3.2 Append-Dominant Structures

* The system **shall support append-dominant mutation patterns** where applicable.
* Destructive updates in such structures **shall be minimised or auditable**.

---

#### 5.3.3 Static Corpora Integrity

* The system **shall treat static corpora as immutable after stabilisation**.
* Any modification **shall be detectable via integrity mechanisms**.

#### 5.3.4 Conflict Resolution

* Conflict detection and resolution are delegated to underlying tools; the system guarantees visibility of divergence but does not enforce automatic resolution.

---

### 5.4 Durability and Replication

#### 5.4.1 Baseline Durability

* The system **shall maintain at least one complete off-site replica** of canonical data.
* This replica **shall be sufficient to recover the canonical dataset** to the state of the most recent completed rotation.

---

#### 5.4.2 Recent Change Protection

* The system **shall provide protection for recent canonical changes** occurring between off-site replications.
* This protection **shall be incremental relative to the baseline replica**.

---

#### 5.4.3 Redundant Off-Site Protection

* The system **shall support redundancy of recent change protection across independent remote providers**.
* Loss of a single remote provider **shall not result in loss of recent protected changes**.

---

#### 5.4.4 Bounded Loss Window

* The system **shall define and enforce a maximum expected loss window** for canonical data not yet incorporated into the baseline replica.
* This window **shall be bounded and observable**.

---

#### 5.4.5 Large Change Handling

* The system **shall provide a mechanism** to reset or reduce incremental replication burden when large changes occur.
* Such mechanisms **shall preserve durability without unbounded resource consumption**.

---

#### 5.4.6 Incremental Bound Enforcement

* The system shall detect excessive growth of incremental replication relative to defined bounds.
* The system shall support operator intervention to reset the incremental base, typically via baseline rotation.
* The system shall support re-initialisation of incremental replication following failure or inconsistency.

---

### 5.5 Integrity Assurance

#### 5.5.1 End-to-End Integrity

* The system **shall provide mechanisms to detect silent corruption** of canonical data.
* Integrity verification **shall not depend solely on storage-layer guarantees**.

---

#### 5.5.2 Static Data Verification

* Static corpora **shall be verifiable against an authoritative integrity record**.
* Integrity records **shall be updateable incrementally**.

---

#### 5.5.3 Verification Capability

* The system **shall support verification of stored data against integrity records** on demand and through defined processes.

---

### 5.6 Recovery Capability

#### 5.6.1 Baseline Recovery (Point-in-Time)

* The system **shall support recovery of canonical data using only off-site baseline replicas**.
* This recovery **shall restore the system to the state of the most recent completed rotation** and **does not include recent changes**.

---

#### 5.6.2 Complete Recovery (Including Recent Changes)

* The system **shall support recovery of canonical data including recent changes** when both baseline replicas and recent change protection are available.

---

#### 5.6.3 Partial Recovery

* The system **shall support selective restoration** of subsets of canonical data without requiring full system restoration.

---

#### 5.6.4 Independent Recovery Materials

* The system **shall maintain a minimal set of recovery artefacts** sufficient to re-establish access to canonical data.
* These artefacts **shall be independently distributable**.

#### 5.6.5 Recovery Capability

* Successful recovery establishes new canonical authority once integrity and completeness checks have passed.

---

### 5.7 Service-Backed Data

#### 5.7.1 Local Mirror

* The system **shall maintain local canonical representations** of service-backed data where feasible.

---

#### 5.7.2 Provider Independence

* The system **shall provide mechanisms such that external services are not the sole retention mechanism** for canonical data.

---

#### 5.7.3 Controlled Deletion

* The system **shall support staged or deferred deletion semantics** where upstream services impose destructive operations.

---

### 5.8 Operational Control

#### 5.8.1 Stewardship Actions

* The system **shall provide defined mechanisms** to perform stewardship actions affecting durability and integrity.
* These actions **shall be repeatable and verifiable**.

---

#### 5.8.2 Observability

* The system **shall provide mechanisms to observe operational state relevant to durability, integrity, and reconciliation**.
* Observability should be implemented using simple, text-based status outputs (e.g. command-line summaries or reports).
* The system shall surface violations of defined operational bounds, including but not limited to:

  * replication lag beyond RPO targets,
  * age of unreconciled transient authoritative state,
  * overdue baseline rotation,
  * integrity verification delays.

---

#### 5.8.3 Bounded Manual Burden

* Routine system operation **shall conform to one of the following classes**:

  * **zero-touch**
  * **one-command**
  * **checklist-driven**
  * **bounded-craft** (ad hoc but constrained and recoverable)

* Operations outside these categories **shall be considered non-compliant**.

---

## 6. Non-Functional Requirements

### 6.1 Durability Constraints

#### 6.1.1 Recovery Point Objective (RPO)

* The system **shall limit expected data loss for canonical data** to:

  * **≤ 1 hour** under normal operation.
* The system **shall support operator-triggered reduction** of this window during periods of intensive work.

RPO guarantees apply only to canonical data that has entered the durability pipeline (e.g. replicated or included in incremental protection). Transient authoritative state that has not been reconciled or captured remains outside durability guarantees and is considered at risk.

---

#### 6.1.2 Baseline Replication Interval

* The system **shall maintain off-site baseline replicas** with a maximum interval between completed rotations of:

  * **≤ 30 days**.
* Shorter intervals **should be used where feasible**.

---

#### 6.1.3 Incremental Replication Continuity

* Incremental replication **shall remain bounded in size and duration** between baseline rotations.
* The system **shall not depend on unbounded incremental chains** for recovery.

---

#### 6.1.4 Replication Failure Tolerance

* Loss of any single replication target **shall not result in loss of protected canonical data within the defined RPO window**.

---

### 6.2 Integrity Constraints

#### 6.2.1 Integrity Verification Coverage

* The system **shall support verification of all canonical data**.
* Static corpora **shall be fully verifiable via authoritative integrity records**.

---

#### 6.2.2 Verification Interval

* Full integrity verification **should occur at intervals not exceeding**:

  * **≤ 90 days**.
* The system **shall support targeted verification on demand**.

---

#### 6.2.3 Detection Guarantee

* ~~The system **shall ensure that silent corruption is detectable prior to propagation across all replicas where feasible**.~~

* Integrity mechanisms **shall minimise the probability and duration of undetected corruption prior to replication and across replicas**.
    
* Early checksum capture at ingestion is preferred where feasible.

---

### 6.3 Recovery Constraints

#### 6.3.1 Recovery Time Objective (RTO)

* Baseline recovery **shall be achievable within**:

  * **≤ 72 hours** from initiation.

* Complete recovery **should be achievable within comparable bounds**, subject to network constraints.

---

#### 6.3.2 Recovery Independence

* Recovery **shall not depend on any single client device**.
* Recovery **shall be achievable using only off-site replicas and independent recovery artefacts**.

---

### 6.4 Operational Constraints

#### 6.4.1 Human Burden Budget

* Routine operations **shall conform to one of the following classes**:

  * zero-touch
  * one-command
  * checklist-driven
  * bounded-craft

* Operations outside these categories **shall be considered non-compliant**.

---

#### 6.4.2 Cognitive Load

* The system **shall minimise reliance on operator memory of implicit procedures**.
* Required actions **shall be documented or discoverable**.

---

#### 6.4.3 Error Tolerance

* The system **shall tolerate routine operator errors** without irreversible data loss where feasible.
* Recovery mechanisms **shall exist for common destructive actions**.

---

### 6.5 Storage and Resource Constraints

#### 6.5.1 Storage Efficiency

* The system **shall avoid unnecessary duplication of large data sets**.
* Large items **should be stored once and referenced logically**.

---

#### 6.5.2 Cloud Storage Constraints

* Cloud usage **shall remain within defined capacity limits**.
* The system **shall provide mechanisms to reduce utilisation when approaching limits**.

---

#### 6.5.3 Bandwidth Constraints

* Replication **shall operate within available bandwidth** without requiring continuous high-throughput connectivity.
* The system **shall tolerate intermittent connectivity**.

---

### 6.6 Service Dependency Constraints

#### 6.6.1 External Service Dependence

* External services **shall not constitute the sole retention mechanism** for canonical data.

---

#### 6.6.2 Provider Failure Tolerance

* Failure of a single external service **shall not result in permanent loss of canonical data**.

---

### 6.7 Security Constraints

#### 6.7.1 Confidentiality of Sensitive Data

* Sensitive canonical data **shall be protected against unauthorised access**.
* Protection mechanisms **shall remain compatible with backup and recovery**.

---

#### 6.7.2 Key Material Availability

* Required credentials and decryption material **shall be recoverable via independent recovery artefacts**.

#### 6.7.3 Security Constraints

* Client compromise is assumed possible; the canonical encrypted store remains the authoritative source of secrets.

---

### 6.8 Lifecycle Constraints

#### 6.8.1 Provisional Retention Bound

* Provisional canonical material **should not remain unreviewed beyond**:

  * **≤ 12 months**.

* The system **shall support identification of items exceeding this bound**.
* The system **shall support identification and reporting of items exceeding this bound**.

---

#### 6.8.2 Transient State Bound

* Transient authoritative state **should not persist beyond**:

  * **≤ 24 hours** under normal operation.

* Extended persistence **shall be detectable via observability mechanisms**.

---

### 6.9 Observability Constraints

#### 6.9.1 State Visibility

* The system **shall expose sufficient information** to determine:

  * replication recency,
  * integrity verification status,
  * age of last baseline rotation,
  * presence of unreconciled transient state.

---

#### 6.9.2 Failure Visibility

* Failures in replication, verification, or recovery processes **shall be detectable within a bounded time frame**.

Violations of defined operational bounds shall be detectable within a bounded time frame.

---

## 7. Operational Policy

This section defines the rules governing how the system is used and maintained.
It translates principles and requirements into enforceable operator behaviour.

---

### 7.1 Canonical Admission Policy

* Information shall not be considered canonical until admitted into a governed class.
* Admission into a canonical class shall imply immediate protection obligation.
* Provisional status shall not reduce protection obligations once admitted.

---

### 7.2 Canonical Authority Policy

* Canonical authority shall reside server-side for all canonical classes.
* Client-side state shall not be treated as canonical authority beyond transient authoritative state.
* All transient authoritative state shall be reconciled into canonical classes within defined bounds.

---

### 7.3 Transient State Policy

* Transient authoritative state shall be:

  * bounded in duration,
  * limited in scope,
  * regularly reconciled.
* The system shall not permit indefinite accumulation of unreconciled transient state.
* Transient state shall be considered at risk until reconciled.

---

### 7.4 Provisional Content Policy

* Provisional content shall be:

  * protected at canonical levels once admitted,
  * subject to deferred classification,
  * regularly reviewed for promotion, retention, or disposal.
* Provisional designation shall not be used to justify neglect or reduced protection.

---

### 7.5 Static Material Policy

* Static material shall:

  * enter through controlled intake (pile),
  * be subject to checksum registration,
  * remain mutable only during early intake where necessary.
* Static material shall become immutable upon promotion to archival classes.
* Duplicate storage of large static items shall be avoided.

---

### 7.6 Version Control Policy

* Mutable repositories shall use version control where practical.
* Canonical history shall be preserved indefinitely unless explicitly pruned by policy.
* Server-side repositories shall be the authoritative reconciliation point.
* Persistent server working copies shall be avoided unless explicitly justified.

---

### 7.7 Integrity Policy

* All canonical data shall be protected by integrity mechanisms.
* Static corpora shall be covered by manifest-based checksum validation.
* Integrity verification shall be performed periodically as a stewardship action.
* Integrity failures shall trigger investigation and recovery procedures.

---

### 7.8 Replication and Backup Policy

* Canonical data shall be replicated to off-site baseline storage.
* Recent changes shall be protected through incremental off-site replication.
* Cloud replication shall remain incremental relative to the last baseline rotation.
* Large changes shall trigger operational intervention (e.g. forced rotation).
* Excessive growth of incremental replication shall trigger operator intervention, typically through forced baseline rotation.
* Failure or breakdown of incremental replication shall trigger corrective action, including re-seeding of the incremental chain, typically via baseline rotation.


---

### 7.9 Service Dependence Policy

* Service-backed data shall be:

  * mirrored locally,
  * archived independently of provider retention.
* External services shall not be treated as sole custodians of canonical data.
* Local mirrors should preserve complete data fidelity where supported by provider interfaces.

---

### 7.10 Stewardship Policy

* Stewardship actions shall:

  * follow defined procedures,
  * be periodically executed,
  * be verifiable.
* Failure to perform stewardship actions shall be treated as system degradation.

---

### 7.11 Semantic Work Policy

* Semantic actions shall prioritise:

  * clarity,
  * reversibility,
  * consistency with the information model.
* The system shall support safe execution of complex transformations.
* High-risk transformations shall be staged or reversible where possible.

---

### 7.12 Human Burden Policy

* Routine operations shall conform to defined burden classes:

  * zero-touch,
  * one-command,
  * checklist-driven,
  * bounded-craft.
* No critical operation shall depend on undocumented or ad-hoc procedure.

---

## 8. Core Workflows

This section defines repeatable processes that implement the operational policy.

---

### 8.1 Capture Workflow

### Purpose

Admit new information into governed classes with minimal friction.

### Process

1. Information is created or acquired on a client or server.
2. Information is placed into an intake path:

   * static → pile
   * project → working repository
   * admin → server-native location
3. Capture command or mechanism transfers data to server if required.
4. Data becomes canonical upon successful admission.

### Properties

* Must be one-command or zero-touch.
* Must not require prior classification.
* Must ensure immediate protection obligation.

---

### 8.2 Reconciliation Workflow (Transient State Closure)

#### Purpose

Resolve transient authoritative state into canonical authority.

#### Process

1. Detect transient state (e.g. client edits).
2. Reconcile via:

   * commit + push (projects),
   * direct write (server-native),
   * sync/import (service-backed).
3. Confirm canonical state updated.

#### Properties

* Must occur within defined time bounds (RPO-driven).
* Must be low-friction during active work.
* Failure leaves data at risk.

---

### 8.3 Static Intake and Curation Workflow

#### Purpose

Manage deferred classification of static material.

#### Process

1. Files enter pile.
2. Files are optionally:

   * renamed,
   * reorganised,
   * lightly corrected (metadata only).
3. Checksums recorded/updated.
4. Periodic review:

   * classify into filing or collections,
   * or discard.

#### Properties

* Must support bulk operations.
* Must allow text-based manipulation where possible.
* Must not require immediate classification.

---

### 8.4 Static Promotion Workflow

#### Purpose

Move mature static material into archival classes.

#### Process

1. Identify items exceeding incubation threshold or ready for classification.
2. Move to:

   * filing (date-based),
   * collections (topic-based).
3. Enforce immutability.
4. Update manifest.

#### Properties

* Must be reversible prior to immutability enforcement.
* Must maintain integrity continuity.

---

### 8.5 Project Workflow

#### Purpose

Manage mutable work with canonical history.

#### Process

1. Create or clone repository.
2. Perform work on client or server.
3. Regularly:

   * commit,
   * push to server.
4. Server maintains canonical history.

#### Properties

* Supports multi-client reconciliation.
* Encourages small, frequent commits.
* Large or atypical projects may follow modified protection paths.

---

### 8.6 Communication Synchronisation Workflow

#### Purpose

Maintain local canonical mirrors of service-backed communication.

#### Process

1. Sync from provider to local mirror.
2. Capture local-origin messages via provider sync.
3. Periodically archive older items.
4. Apply retention policy on provider.

#### Properties

* Must preserve full local copy independent of provider.
* Must tolerate provider inconsistency.
* Must distinguish mirror vs archive roles.

---

### 8.7 Backup Rotation Workflow

#### Purpose

Maintain off-site baseline durability.

#### Process

1. Snapshot canonical datasets.
2. Replicate to removable storage.
3. Physically rotate storage off-site.
4. Verify integrity periodically.

#### Properties

* Checklist-driven.
* Must be verifiable.
* Defines baseline recovery point.

---

### 8.8 Cloud Replication Workflow

#### Purpose

Protect recent changes between baseline rotations.

#### Process

1. Detect incremental changes since last baseline.
2. Replicate to cloud providers.
3. Maintain incremental chain.
4. Monitor size and growth.

#### Properties

* Must remain incremental.
* Must meet RPO targets (~1 hour baseline).
* Must support manual triggering for high-risk work.

---

### 8.9 Recovery Workflow

#### Purpose

Restore system from failure scenarios.

#### Modes

##### Baseline Recovery

* Restore from off-site replica only.
* Recovers to last rotation point.

##### Complete Recovery

* Restore baseline.
* Apply incremental cloud changes.

#### Properties

* Must be documented and testable.
* Must not depend on unavailable local state.

---

### 8.10 Stewardship Workflow

#### Purpose

Maintain system health over time.

#### Includes

* integrity checks,
* manifest verification,
* replication monitoring,
* SOS regeneration,
* audit of transient state backlog.

#### Properties

* Checklist-driven.
* Periodic.
* Failure is silent but cumulative.

---

### 8.11 Bounded-Craft Workflow

#### Purpose

Enable safe execution of complex, non-routine transformations.

Bounded-craft operations must be staged and reversible where feasible.

#### Process

1. Define transformation (script, command sequence, or manual procedure).
2. Stage operation:

   * preview changes,
   * test on subset.
3. Execute transformation.
4. Verify results.
5. Commit changes to canonical state.

#### Properties

* Explicitly non-routine but controlled.
* Must be reproducible where feasible.
* Must avoid irreversible bulk damage.

---

## 9. Acceptance Criteria

This section defines how each functional (Section 5) and non-functional (Section 6) requirement is verified.

Each requirement is mapped to one or more acceptance tests that are:

* observable,
* repeatable,
* minimally ambiguous.

---

### 9.1 Acceptance Mapping Rules

* Every requirement in Sections 5 and 6 shall have at least one acceptance test.
* Acceptance tests may validate multiple related requirements where appropriate.
* Each test must:

  * specify setup,
  * specify action,
  * specify observable outcome.

---

## 9.2 Functional Requirement Acceptance

---

### 9.2.1 Canonical Admission (5.1.1)

**Test: Admission Completeness**

* Setup: create new data on client.
* Action: execute capture workflow.
* Verify:

  * data exists in canonical location,
  * data included in snapshot scope,
  * data included in replication scope.

---

### 9.2.2 Canonical Authority (5.1.2)

**Test: Authority Uniqueness**

* Select dataset.
* Verify:

  * authoritative location identifiable,
  * no competing canonical source exists.

---

### 9.2.3 Transient State Identification (5.1.3)

**Test: Divergence Visibility**

* Setup: modify file locally without reconciliation.
* Verify:

  * system exposes unsynchronised state (e.g. git status, sync diff).

---

### 9.2.4 Transient State Reconciliation (5.1.3)

**Test: Reconciliation Integrity**

* Setup: create local changes.
* Action: reconcile (commit/push/sync).
* Verify:

  * changes present in canonical store,
  * no data loss,
  * history updated.

---

### 9.2.5 Static Intake (5.2.1)

**Test: Intake Admission**

* Add files to intake.
* Verify:

  * files appear in pile,
  * included in protection scope.

---

### 9.2.6 Static Promotion (5.2.2)

**Test: Promotion Correctness**

* Move files from pile to archive.
* Verify:

  * files relocated correctly,
  * immutability enforced,
  * manifest updated.

---

### 9.2.7 Static Immutability (5.2.3)

**Test: Immutability Enforcement**

* Attempt modification of archived file.
* Verify:

  * modification blocked or detectable as violation.

---

### 9.2.8 Manifest Maintenance (5.2.4)

**Test: Incremental Update**

* Modify static dataset.
* Verify:

  * only affected entries updated,
  * manifest remains consistent.

---

### 9.2.9 Manifest Integrity Detection (5.2.5)

**Test: Corruption Detection**

* Alter file contents.
* Run verification.
* Confirm mismatch detected.

---

### 9.2.10 Version Control Usage (5.3.1)

**Test: Repository Presence**

* Inspect project datasets.
* Verify:

  * version control present where applicable.

---

### 9.2.11 Canonical Repository Authority (5.3.2)

**Test: Server Authority**

* Verify:

  * canonical repo resides server-side,
  * client repos are non-authoritative.

---

### 9.2.12 Multi-Client Reconciliation (5.3.3)

**Test: Merge Preservation**

* Create divergent changes on two clients.
* Merge.
* Verify:

  * both changes preserved.

---

### 9.2.13 Baseline Replication (5.4.1)

**Test: Replica Completeness**

* Perform rotation.
* Verify:

  * datasets present on off-site storage,
  * snapshot consistency maintained.

---

### 9.2.14 Incremental Replication (5.4.2)

**Test: Incremental Behaviour**

* Modify small data.
* Verify:

  * only delta transferred,
  * no full re-sync.

---

### 9.2.15 Dual-Provider Replication (5.4.3)

**Test: Redundant Presence**

* Verify:

  * recent deltas exist on both providers.

---

### 9.2.16 Baseline Recovery (5.5.1)

**Test: Baseline Restore**

* Simulate total server loss.
* Restore from HDD.
* Verify:

  * system operational at last rotation point.

---

### 9.2.17 Complete Recovery (5.5.2)

**Test: Full Restore**

* Restore baseline.
* Apply cloud deltas.
* Verify:

  * recent changes present.

---

### 9.2.18 Service Synchronisation (5.6.1)

**Test: Mirror Accuracy**

* Sync service data.
* Verify:

  * local mirror matches provider state.

---

### 9.2.19 Service Independence (5.6.2)

**Test: Offline Access**

* Disable provider access.
* Verify:

  * local data remains accessible.

---

### 9.2.20 Provider Retention Independence (5.6.3)

**Test: Archive Persistence**

* Remove old data from provider.
* Verify:

  * data still exists locally.

---

### 9.2.21 Low-Friction Capture (5.7.1)

**Test: Capture Simplicity**

* Perform capture.
* Verify:

  * achievable in ≤ one command or automated.

---

### 9.2.22 Routine Operation Simplicity (5.7.2)

**Test: Workflow Execution**

* Execute standard workflows.
* Verify:

  * no multi-step undocumented procedure required.

---

### 9.2.23 Bounded Manual Burden (5.7.3)

**Test: Documentation Completeness**

* Attempt workflows using documentation only.
* Verify:

  * no missing steps.

---

## 9.3 Non-Functional Requirement Acceptance

---

### 9.3.1 RPO Compliance (6.1.1)

**Test: Recovery Point Bound**

* Introduce change.
* Simulate failure at intervals.
* Verify:

  * worst-case loss ≤ defined RPO (~1 hour).

---

### 9.3.2 Recovery Time Acceptability (6.1.2)

**Test: Recovery Execution**

* Perform full recovery.
* Verify:

  * completes within acceptable human-tolerable window.

---

### 9.3.3 Integrity Coverage (6.2.1)

**Test: Coverage Audit**

* Inspect datasets.
* Verify:

  * all canonical data covered by checksumming or equivalent.

---

### 9.3.4 Integrity Verification Frequency (6.2.2)

**Test: Verification Execution**

* Review logs.
* Verify:

  * periodic integrity checks performed.

---

### 9.3.5 Workflow Classification (6.3.1)

**Test: Burden Classification**

* Inspect workflows.
* Verify:

  * each classified as:

    * zero-touch,
    * one-command,
    * checklist,
    * bounded-craft.

---

### 9.3.6 Human Burden Limits (6.3.2)

**Test: Effort Bound**

* Execute workflows.
* Verify:

  * time and cognitive load consistent with classification.

---

### 9.3.7 Documentation Sufficiency (6.4.1)

**Test: Cold Execution**

* Execute tasks without prior memory.
* Verify:

  * documentation alone sufficient.

---

### 9.3.8 No Hidden Knowledge Dependency (6.4.2)

**Test: Transferability**

* Have second operator (or simulated “future you”) execute.
* Verify:

  * no hidden assumptions required.

---

### 9.3.9 Resource Constraint Compliance (6.5.1)

**Test: Storage Bound**

* Measure storage usage.
* Verify:

  * within defined limits (SSD, HDD, cloud).

---

### 9.3.10 Incremental Efficiency (6.5.2)

**Test: Delta Efficiency**

* Perform repeated updates.
* Verify:

  * replication remains incremental and bounded.

---

### 9.3.11 Operational Stability (6.6.1)

**Test: Routine Operation**

* Run system over extended period.
* Verify:

  * no accumulation of unresolved transient state,
  * no silent degradation.

---

### 9.4 Acceptance Completion Condition

The system is accepted as compliant when:

* every requirement in Sections 5 and 6 has been exercised by at least one acceptance test,
* recovery scenarios succeed,
* integrity violations are detectable,
* workflows execute within defined burden limits,
* no requirement depends on undocumented behaviour.

---

## 10. Implementation Notes

This section provides guidance for a concrete implementation of the system described in this specification.

It does not redefine requirements, but records:

* inferred design constraints,
* preferred mechanisms,
* known trade-offs,
* operational heuristics.

Where implementation choices materially affect authority, durability, or workflow behaviour, they are described here.

---

### 10.1 Storage Architecture

#### 10.1.1 Filesystem

A filesystem with the following properties is strongly implied:

* end-to-end checksumming,
* snapshot support,
* efficient incremental replication,
* copy-on-write semantics.

**ZFS** is the reference implementation due to:

* native integrity guarantees,
* atomic snapshots,
* send/receive replication model.

Equivalent systems may be used if they satisfy the same properties.

---

#### 10.1.2 Dataset Layout

Datasets are **policy boundaries**, not organisational folders.

Datasets should be created only where differences exist in:

* snapshot frequency,
* retention policy,
* replication behaviour,
* mutation profile.

Typical dataset structure:

```
active/
  server
  projects
  pile
  spool

archive/
  filing
  collections

stash/
```

Avoid over-segmentation. Each additional dataset increases operational burden.

---

#### 10.1.3 Snapshot Strategy

* Snapshots should be:

  * frequent for active datasets,
  * less frequent for archival datasets.
* Recursive snapshots are acceptable and atomic.
* Snapshot naming should be consistent and sortable.

Snapshots are the primary protection against:

* user error,
* short-term corruption.

---

### 10.2 Replication Architecture

#### 10.2.1 Baseline Replication (HDD Rotation)

* Primary durability baseline is:

  * replication to removable HDD,
  * physically rotated off-site.
* Rotation frequency defines baseline recovery point.

Operational notes:

* Maintain at least one off-site copy at all times.
* Prefer two rotating drives for redundancy.
* Periodically verify replica integrity.

---

#### 10.2.2 Incremental Cloud Replication

Cloud replication provides protection for changes since last rotation.

Key constraints:

* replication must remain incremental,
* transfer volume must remain bounded.

Operational model:

1. replicate baseline to HDD,
2. subsequent changes replicated to cloud,
3. rotation resets incremental base.

---

#### 10.2.3 Cloud Provider Redundancy

* Use at least two independent providers.
* Replication streams should be logically independent.
* Failure of one provider must not compromise recovery.

---

#### 10.2.4 Large Data Handling

Large datasets require special handling:

* initial bulk transfer performed once,
* subsequent deltas must remain small.

If deltas grow too large:

* force HDD rotation,
* avoid attempting large cloud transfers.

This is a **discipline problem**, not a tooling problem.

---

### 10.3 Version Control Strategy

#### 10.3.1 Canonical Repositories

* Canonical git repositories reside on server.
* Use bare repositories where appropriate.
* Server acts as reconciliation point.

---

#### 10.3.2 Working Copies

* Client working copies are normal.
* Persistent server working copies should be avoided unless justified.

Reason:

* multiple working copies increase cognitive overhead,
* risk of divergence.

---

#### 10.3.3 Commit Discipline

* Encourage small, frequent commits.
* Push regularly to minimise transient risk.
* Avoid large uncommitted working states.

---

### 10.4 Static File Management

#### 10.4.1 Intake Mechanism

Static files should be captured via:

* client-side staging area (e.g. inbox),
* transfer command to server pile.

Capture should:

* minimise friction,
* avoid premature classification.

---

#### 10.4.2 Pile Management

* Pile is a high-churn dataset.
* Supports:

  * renaming,
  * reorganisation,
  * light metadata correction.

Avoid:

* repeated heavy mutation,
* duplicate storage.

---

#### 10.4.3 Promotion to Archive

* Promotion should be:

  * periodic,
  * reversible prior to finalisation.
* Filing:

  * date-based structure.
* Collections:

  * topic-based structure.

After promotion:

* enforce read-only where practical.

---

#### 10.4.4 Manifest Implementation

Manifest requirements:

* per-file checksum,
* incremental updates,
* version controlled.

Implementation approaches:

* append/update on file changes,
* avoid full re-scan where possible.

Trade-off:

* incremental complexity vs full regeneration cost.

---

### 10.5 Communication Streams

#### 10.5.1 Email

* Local storage via **Maildir**.
* Sync from IMAP provider.

Important nuance:

* locally authored messages may arrive via provider,
* provenance may appear remote despite local authorship.

Retention:

* recent mail remains on provider,
* older mail archived locally.

---

#### 10.5.2 Contacts and Calendar

* Mirror via:

  * CardDAV (contacts),
  * CalDAV (calendar).
* Store as:

  * VCARD,
  * iCalendar.

Low volume, but high importance.

---

#### 10.5.3 Client Access

* GUI access handled via provider services.
* Local store provides:

  * independence,
  * archival integrity.

---

### 10.6 Peripheral Capture (Stash)

#### 10.6.1 Purpose

* Temporary capture of unmanaged client data.
* Migration scaffold, not canonical storage.

---

#### 10.6.2 Mechanism

Typical approach:

```
rsync -a <client_subset> server:/store/stash/rsync-$HOST/
```

---

#### 10.6.3 Limitations

* No integrity guarantees by default.
* Possible silent corruption.

Mitigations:

* periodic checksum runs,
* occasional `--checksum` syncs.

---

#### 10.6.4 Deletion Policy

* Explicit decision required:

  * mirror mode (`--delete`),
  * accumulation mode.

Avoid ambiguity.

---

### 10.7 Integrity Strategy

#### 10.7.1 Layered Integrity

Integrity is provided by:

* filesystem (ZFS),
* version control (git),
* manifest (static files).

Each layer serves different data classes.

---

#### 10.7.2 Verification

* periodic verification required:

  * scrubs (filesystem),
  * manifest checks,
  * repo validation.

---

### 10.8 Secrets Management

#### 10.8.1 Storage

* Store secrets as encrypted files (e.g. pass-style).
* Version controlled with caution.

---

#### 10.8.2 Client Integration

* Convenience stores (Keychain, KeePassXC) may be used.
* Client-side convenience stores are considered operational replicas, not trusted authorities.
* Synchronisation is:

  * manual,
  * checklist-driven.




---

#### 10.8.3 Rotation

* Secrets should have:

  * expiry metadata,
  * rotation workflow.

---

### 10.9 SOS Pack

#### 10.9.1 Purpose

* Minimal recovery bundle for catastrophic failure.

---

#### 10.9.2 Contents

* credentials,
* critical documents,
* recovery instructions.

---

#### 10.9.3 Generation

* Generated from source repository.
* Trigger regeneration when:

  * secrets change,
  * recovery procedures change.

---

#### 10.9.4 Distribution

* Stored externally to primary system.
* Accessible without system recovery.

---

### 10.10 Tooling Philosophy

#### 10.10.1 CLI-First

Primary interfaces:

* shell,
* ssh,
* text editor.

---

#### 10.10.2 Text as Control Surface

Prefer:

* text-based configuration,
* text-based metadata,
* scriptable workflows.

---

#### 10.10.3 Safe Transformation Tools

Encourage tools such as:

* `vidir`-style batch editing,
* dry-run capable scripts,
* preview-before-apply workflows.

---

### 10.11 Operational Automation

#### 10.11.1 Automation Targets

Automate:

* snapshots,
* replication,
* integrity checks.

---

#### 10.11.2 Manual Control Points

Keep manual:

* classification,
* archival decisions,
* large transformations.

---

### 10.12 Known Trade-offs

#### 10.12.1 Simplicity vs Flexibility

* Simpler workflows reduce error.
* Flexibility retained via bounded-craft operations.

---

#### 10.12.2 Cost vs Durability

* Full redundancy everywhere is impractical.
* Selective replication is required.

---

#### 10.12.3 Discipline vs Automation

* Some guarantees require human discipline.
* System encodes discipline but cannot enforce it completely.

---

### 10.13 Non-Goals (Implementation Level)

The system deliberately avoids:

* full device imaging,
* real-time multi-device sync,
* complex distributed systems,
* heavy metadata indexing,
* high-availability infrastructure.

---

