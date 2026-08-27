<!-- GENERATED FILE - DO NOT EDIT DIRECTLY.
Governance framework: 1.1.0
Model: controlled-production@1.0.0
Manifest: 00_Governance/projects/astv/manifest.json
Rendered payload SHA-256: 1f23314f87875f6116d91b0170a40f238fe5bcdfcb4af6abe046e331c3049698
Regenerate with: 00_Governance/tooling/Render-Governance.ps1
-->


# ASTV Architecture Governance

These instructions apply within `ASTV/01_Architecture/` and are self-contained;
they do not rely on Git-root instruction inheritance.

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

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/architecture/1.0.0.md -->
## Architecture capability 1.0.0

Architecture documentation defines responsibilities, boundaries, major flows,
interfaces, decisions, and constraints. It is not a scratchpad for unlabeled
ideas.

Before an architecture change, read current production evidence, applicable
contracts, current architecture, project governance, and relevant historical
context. Classify the change as current-state correction, approved target
design, or exploratory proposal. Do not invent architecture for implementation
or diagramming convenience.

Written architecture and diagrams must agree. If they do not, identify the
conflict, resolve it against higher-precedence evidence, update only the
appropriate artifact, and leave remaining uncertainty explicit.

Show product boundaries, ownership, calls, return data, external systems, and
data sources clearly. Preserve established visual conventions and manual layout.
Architecture determines canvas size; canvas size never determines architecture.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/architecture/1.0.0.md -->

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

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/drawio-strict/1.0.0.md -->
## Strict draw.io capability 1.0.0

The saved `.drawio` file is the visual source of truth for established geometry
and phase layout. Only one editor may be active. Before Codex edits it, the user
must save and close it or confirm it will not be saved concurrently; Codex must
then reread the latest file. After editing, save before reporting and have the
user reopen the saved file.

Never move, resize, rename, delete, restyle, reroute, compact, crop, center,
symmetrize, or clean up an existing object unless the approved change requires
it. Expand the canvas and preserve deliberate whitespace instead of compressing
architecture. A governance change alone never grants diagram-edit permission.
Do not export PNG or PDF unless requested.

### Flow and layout

- Primary lifecycle flow is left-to-right across explicit vertical phase bands.
- Components remain in their architectural phase; branches may move vertically
  within a phase and then continue left-to-right.
- Supporting functions, gateways, data sources, and returns form readable local
  clusters around the component that actually calls them.
- Do not connect sibling functions merely because they execute in sequence.
- Local grouping and readable routing outrank global symmetry or mathematical
  centering. Whitespace is elastic and intentional.
- External execution paths should leave their caller horizontally where
  practical. Data sources stay close to their consumer and are not independent
  execution branches.

### Gateways

Use a compact diamond only for a genuine control-flow gateway:

- exclusive split: one incoming and mutually exclusive outgoing branches, named
  `gateway_split_<purpose>`;
- exclusive merge: multiple mutually exclusive inputs and one output, named
  `gateway_merge_<purpose>`; it is convergence only, not a script, function,
  transformer, or consolidator; and
- parallel/synchronizing: genuine parallel completion or synchronization,
  visibly marked `+`, named `gateway_parallel_<purpose>`.

Split and merge gateways may be offset for clean routing. Do not use a parallel
gateway merely because a caller invokes several functions.

### Connectors and labels

- One function invocation uses one solid directional call connector.
- One function return uses a separate dashed connector. Never use a double-headed
  connector and never invent a return.
- Each passed or returned variable uses its own bordered native connector label;
  do not create one connector per variable, combine variables in one label, or
  use detached label shapes.
- Preserve exact architectural/YAML names; do not normalize capture and return
  names.
- Decision outcomes are native labels on outgoing connectors, placed close to
  the gateway so they remain attached when objects move.
- Prefer straight or simple orthogonal routes, clean shared trunks, and 90-degree
  turns. Avoid unnecessary diagonals, bends, waypoints, crossings, and wide
  return loops.
- Keep call and return routes visually distinct; use an outside return lane when
  needed.

For a horizontal primary pipeline, place separate payload labels above the
receiving component, top-left aligned, vertically stacked, individually bordered,
and clear of both the component and connector. Supporting towers retain their
local connector-label convention.

Copy styles from existing approved objects. Preserve the visual hierarchy:
primary pipeline dominant; support functions and data sources subordinate;
gateways compact; external actions distinct.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/drawio-strict/1.0.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/projects/astv/architecture-overlay.md -->
## ASTV architecture overlay

`ASTV/01_Architecture/ASTV_Architecture.drawio` is the authoritative visual
structure and phase layout. The live Home Assistant configuration is
authoritative for entity IDs, inputs, response variables, service calls, and
dependencies. `ASTV/01_Architecture/ASTV_ARCHITECTURE.md` is the semantic record.

Use the established styling:

- blue: main ASTV pipeline scripts;
- green: supporting functions and providers;
- yellow: data sources;
- purple: external actions;
- neutral grey: Home Assistant entities; and
- grey hexagon: an external subsystem.

ASTV script/function boxes show the friendly name and technical entity ID.
Decision diamonds use the established compact 50x50 baseline and must not be
enlarged without explicit approval.

Preserve the cross-functional phase bands and manually corrected layout. Phase 3
execution branches may occupy separate local regions and must not be forced into
equal vertical lanes. The ASTV diagram may show the AdvMedia adapter and external
subsystem, but never AdvMedia's internal function chain.

Typical branch outcomes include `Media`, `Routine`, `HA Media Player`, `Google
Home Device`, `AdvMedia`, and `Radio Browser`; keep each label attached to its
originating connector.
<!-- END GOVERNANCE SOURCE: 00_Governance/projects/astv/architecture-overlay.md -->
