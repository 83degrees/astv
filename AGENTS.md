<!-- GENERATED FILE - DO NOT EDIT DIRECTLY.
Governance framework: 1.1.0
Model: controlled-production@1.0.0
Manifest: 00_Governance/projects/astv/manifest.json
Rendered payload SHA-256: b8d1e02f789a328a2cf9e25f93cff9343234af8194da2a9a1ab21bfff5f058e2
Regenerate with: 00_Governance/tooling/Render-Governance.ps1
-->


# ASTV Project Governance

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/core/governance.md -->
## Shared governance

Read every applicable `AGENTS.md` before work. A nested file may add stricter
rules but must not silently weaken project-wide safety, architecture, contract,
or authorization controls.

Before changing anything:

1. identify the approved scope and exact files;
2. inspect the applicable sources of truth;
3. identify affected product owners, interfaces, and consumers;
4. expose conflicts, missing evidence, and material ambiguity instead of
   guessing; and
5. define proportionate validation.

User-authored edits are authoritative unless explicitly superseded. Make the
smallest scoped change. Do not opportunistically reformat, relayout, rename,
move, or refactor unrelated material.

Changes to component ownership, subsystem boundaries, inputs or outputs,
routing, external dependencies, or interface meaning are architecture or
contract changes and require explicit approval.

Chat history and historical handovers preserve context but are not the sole
durable record. Promote approved decisions to current architecture, contracts,
governance sources, or Linear as appropriate.

A task is complete only when implementation is in scope, relevant validation
passes, evidence and limitations are recorded, and no unrelated files or system
state changed.

## Governance change requests

When a governance rule appears missing, incorrect, incomplete, or unsuitable,
do not treat a generated `AGENTS.md` as authoritative or edit it directly. Pause
only the affected unsafe or ambiguous work when necessary, record and link a
Governance CR, and follow
`00_Governance/docs/GOVERNANCE_CHANGE_REQUESTS.md`. A temporary restriction may
narrow or pause authority; it must never grant new authority.
<!-- END GOVERNANCE SOURCE: 00_Governance/core/governance.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/core/source-of-truth.md -->
## Source of truth

When sources disagree, use this precedence:

1. current production evidence;
2. current explicit interface contracts;
3. current subsystem architecture documentation and authoritative diagrams;
4. applicable generated governance instructions;
5. project documentation and current-state summaries;
6. historical or pre-project context;
7. temporary working notes and chat history.

A Linear issue is the approved work instruction, not a source of technical
truth. If its scope or acceptance criteria conflict with a higher-precedence
source, stop and record the conflict rather than silently resolving it.

A copied production snapshot is read-only evidence and is authoritative only as
of its recorded capture. Check provenance, timestamp, completeness, exclusions,
and integrity hashes before relying on it. Prefer verified read-only live
evidence when freshness matters and access is authorized.

Current, approved target, proposed, exploratory, historical, and unresolved
states must be labelled distinctly. Never describe a proposed design as current
production behavior.
<!-- END GOVERNANCE SOURCE: 00_Governance/core/source-of-truth.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/models/controlled-implementation/1.0.0.md -->
## Governance model: controlled-implementation 1.0.0

Implementation is controlled by a hard pickup gate. It cannot begin unless:

1. an eligible `ASTV-...` Linear identifier exists on the shared `astv` team;
2. a separate Codex implementation task has retrieved the full issue;
3. the issue is in `Ready`;
4. scope and acceptance criteria have been checked against the source-of-truth
   hierarchy;
5. no conflict or material ambiguity remains; and
6. that Codex task has moved the issue from `Ready` to `In Progress`.

Creating, refining, approving, or moving an issue to `Ready` in a design task
never authorizes that same task to implement it. Without a valid pickup, limit
work to discussion, read-only investigation, and work-instruction preparation.

After pickup, Codex owns scoped implementation and validation. Before moving the
issue to `Review / Test`, record changed files, validation, results, and unresolved
limitations. Only the user may move it to `Done`.

An explicitly populated and user-activated `CURRENT_WORK.md` is exceptional. If
it conflicts with the Linear instruction, stop and ask which one controls.
<!-- END GOVERNANCE SOURCE: 00_Governance/models/controlled-implementation/1.0.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/models/controlled-production/1.0.0.md -->
## Governance model: controlled-production 1.0.0

All `controlled-implementation` pickup and completion rules apply.

In addition:

- production evidence must be mounted or granted read-only for routine work;
- live Home Assistant access must default to read-only outside an issue whose
  approved scope explicitly requires mutation;
- mutation tools must be enabled only for that separately governed task;
- never deploy, reload, restart, call services, or alter live state unless the
  work instruction explicitly authorizes it; and
- validate locally and statically before any controlled runtime step.

Repository instructions are policy, not a mechanical security boundary. If the
environment exposes broader write capabilities, do not use them outside a valid
pickup and explicitly authorized scope.
<!-- END GOVERNANCE SOURCE: 00_Governance/models/controlled-production/1.0.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/contracts/1.0.0.md -->
## Contract capability 1.0.0

Cross-product interfaces are explicit contracts. A consumer must not depend on
another product's undocumented internals.

Do not rename, add, remove, normalize, reinterpret, or change the requiredness of
fields without reviewing the authoritative contract and every known producer and
consumer. A caller capture-variable name and a child return-field name are
different concepts and must not be made identical merely for consistency.

If a boundary change is required:

1. identify ownership and all known consumers;
2. update the shared contract first or as one coordinated change;
3. keep each product's implementation work separately authorized; and
4. validate compatibility and failure behavior.

Use the central contract registry to record ownership, producers, consumers,
status, version, and relative source path. Architecture may explain a boundary,
but the contract remains authoritative for its precise interface.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/contracts/1.0.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/linear-workflow/1.0.0.md -->
## Linear workflow capability 1.0.0

All three products use the shared Linear team `astv` and the intentional shared
`ASTV-...` issue namespace.

Durable roles are separate:

- **Design task:** discusses requirements, inspects evidence read-only, develops
  design, and prepares or refines the work instruction. It stops after handing
  back the issue identifier.
- **Approved Linear work instruction:** carries scope, acceptance criteria,
  dependencies, and required validation. It does not override technical sources
  of truth.
- **Separate implementation task:** retrieves the issue, satisfies the selected
  model's pickup gate, implements only the approved scope, validates it, and
  records evidence.

Use the shared status meanings:

- `Ready`: approved and eligible for pickup where the model permits.
- `In Progress`: picked up by the implementation task.
- `Review / Test`: implementation and Codex validation complete; ready for user
  review or testing.
- `Done`: final user acceptance only.

Conversational phrases such as “agreed”, “continue”, “go ahead”, or “approved”
approve design or work definition only. They never bypass the Linear boundary.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/linear-workflow/1.0.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/production-evidence/1.0.0.md -->
## Production evidence capability 1.0.0

Production evidence is held outside product repositories under
`Production_ReadOnly/` and must remain read-only. Never modify, rename, delete,
reformat, regenerate, or use it as a working directory. Never sync local changes
back to production.

Before relying on evidence, check its capture timestamp, source, procedure,
included and excluded areas, freshness, and hashes. If evidence is missing,
stale, incomplete, or ambiguous, say so and do not invent behavior. A missing
capture manifest is a limitation to fix in a future capture process, not by
retrospectively editing an existing snapshot.

Governance stores only metadata, SHA-256 hashes, relative references, and compact
validation notes. Credentials, secrets, mutable state, production snapshots, and
large rollback payloads remain outside future version-controlled governance.

Use the production-capture manifest and evidence-index schemas for new captures.
Record exactly what was inspected, what was verified, what remains unverified,
and whether any live read-only evidence supplemented the snapshot.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/production-evidence/1.0.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/projects/astv/root-overlay.md -->
## ASTV product overlay

ASTV is the Home Assistant intent and orchestration product. It owns NFC/tag
entry, request resolution, intent routing, household area/domain preference,
endpoint and playback-method selection, fallback order, and dispatch to the
appropriate execution path.

Read `ASTV/01_Architecture/ASTV_ARCHITECTURE.md` and the applicable contracts.
`ASTV/00_PreProject_History/CONTEXT_HANDOVER.md` is retained historical context
only. Legacy or unused scripts are not current architecture merely because they
remain in configuration.

ASTV may call AdvMedia through `contracts/ASTV_ADVMEDIA_INTERFACE.md`, but must
not expand or depend on AdvMedia internals. Preserve exact interface and response
names across gateways, engines, adapters, providers, and return boundaries.

ASTV production evidence is read-only. No available filesystem or Home Assistant
write capability may be used without an explicitly authorized ASTV issue.
<!-- END GOVERNANCE SOURCE: 00_Governance/projects/astv/root-overlay.md -->
