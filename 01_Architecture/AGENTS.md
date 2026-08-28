<!-- GENERATED FILE - DO NOT EDIT DIRECTLY.
Governance framework: 1.2.0
Model: controlled-production@1.0.0
Manifest: 00_Governance/projects/astv/manifest.json
Rendered payload SHA-256: 2d998434cdf82deb1335289fb5575b3b76e2e1b460328f45f79222f2449d93f2
Regenerate with: 00_Governance/tooling/Render-Governance.ps1
-->


# ASTV Architecture Governance

These instructions apply within `ASTV/01_Architecture/` and are self-contained
for the central Governance rules rendered into this payload. They do not depend
on Git-root instruction inheritance. Read any more-specific applicable nested
`AGENTS.md`; it may add stricter controls but must not silently weaken applicable
central rules.

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

For Git-managed product files, commit history is the technical change history
and diff is the normal comparison. Do not duplicate it with revision logs,
source backups, or equivalent recovery copies. Governed baselines, evidence,
contracts, CR records, and DDRs serve distinct purposes. Linear remains the sole
product work tracker; apply the Git capability only to repositories actually
changed.

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

Subject authority refines, but does not replace, the precedence above:

- production evidence establishes what is actually deployed;
- explicit contracts define precise interfaces;
- the approved product `*_ARCHITECTURE.md` is the semantic architecture record;
- the approved product `*_ARCHITECTURE.drawio` is the visual structure and
  layout record;
- applicable generated governance instructions define agent and governance
  rules in their scope; and
- Git records tracked repository state and technical change history.

For each Git-managed product repository, `main` is the current integrated state
accepted into `main` under the governed workflow. Presence on `main` alone does
not prove final validation, Linear `Done`, or deployed production state.
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

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/architecture/1.1.0.md -->
## Architecture capability 1.1.0

Each product has exactly one approved written architecture document and one
authoritative draw.io diagram. The `*_ARCHITECTURE.md` file is the semantic
architecture record; the matching `*_ARCHITECTURE.drawio` file is the visual
structure and layout record. Supporting documents may explain or validate the
architecture but must not become additional authorities.

Architecture documentation defines responsibilities, boundaries, major flows,
interfaces, decisions, and constraints. It is not a scratchpad for unlabeled
ideas. Before an architecture change, read current production evidence,
applicable contracts, current architecture, applicable governance, materially
applicable DDRs, and relevant historical context. Classify the change as a
current-state correction, approved target design, or exploratory proposal. Do
not invent architecture for implementation or diagramming convenience.

Markdown and draw.io must agree; divergence is a Governance finding. Resolve it
against higher-precedence evidence, update each affected representation, and
leave uncertainty explicit. Architecture work cannot reach `Done` until both
authorities are current and mutually consistent.

Where a DDR materially governs the architecture, reference it in the
architecture Markdown. Do not place DDR references in the diagram. The DDR gate
and every applicable repository Git gate remain cumulative.

Show product boundaries, ownership, calls, return data, external systems, and
data sources clearly. Preserve established visual conventions and manual layout.
Architecture determines canvas size; canvas size never determines architecture.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/architecture/1.1.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/contracts/1.1.0.md -->
## Contract capability 1.1.0

Cross-product interfaces are explicit contracts. A consumer must not depend on
another product's undocumented internals. Authoritative shared contracts live
once under `contracts/`; do not copy them into product repositories or create
parallel contract authorities.

Do not rename, add, remove, normalize, reinterpret, or change the requiredness of
fields without reviewing the authoritative contract and every known producer and
consumer. A caller capture-variable name and a child return-field name are
different concepts and must not be made identical merely for consistency.

If a boundary change is required:

1. identify ownership and all known producers and consumers;
2. update the shared contract first or as one coordinated change;
3. keep each product's implementation work separately authorized; and
4. validate compatibility and failure behavior.

Use the central contract registry to record ownership, producers, consumers,
status, version, and relative source path. Architecture may explain a boundary,
but the contract remains authoritative for its precise interface. A
contract-affecting issue cannot reach `Done` until the authoritative shared
contract is current. Product Git gates apply independently only to product
repositories actually changed; changing only shared contract material does not
create an artificial product-repository commit or push.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/contracts/1.1.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/linear-workflow/1.1.0.md -->
## Linear workflow capability 1.1.0

Linear is the sole product work tracker and work-control record. GitHub Issues
must not be introduced as a parallel ASTV, AdvMedia, or MediaCat backlog. All
three products use the shared Linear team `astv` and the intentional shared
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

When product repositories change, `Done` also requires every affected
repository's committed-`main`, validation, evidence, and push gate. A required
DDR adds its gate. Shared-only work gains no artificial product Git gate. Commit
and DDR references add traceability without replacing Linear.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/linear-workflow/1.1.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/production-evidence/1.1.0.md -->
## Production evidence capability 1.1.0

Production evidence is held outside product repositories under
`Production_ReadOnly/` and must remain read-only. Never modify, rename, delete,
reformat, regenerate, copy it into a product repository, or use it as a working
directory. Never sync local changes back to production.

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
and whether authorized live read-only evidence supplemented the snapshot.

Production evidence, Git state, and validation evidence are distinct.
Validation evidence remains outside individual product repositories and records
the governing Linear issue plus every affected repository and committed SHA.
Final validation must address the committed result; pre-commit checks are not a
substitute. A push proves only remote presence, not validation, approval,
completion, or deployed production state.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/production-evidence/1.1.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/git-workflow/1.0.0.md -->
## Git workflow capability 1.0.0

Git commit history is the authoritative technical change history for ASTV,
AdvMedia, and MediaCat repository files; Git diff is the normal comparison.
`main` is the integrated state accepted under the governed workflow, not proof
of final validation, Linear `Done`, or deployment.

Do not create per-file change logs, before/after copies, dated backups, `.old`,
`.bak`, `.backup`, copied source baselines, or equivalent artefacts whose sole
purpose duplicates Git history. Governance baselines, evidence, contracts, CR
records, and DDRs are distinct exceptions.

Apply this gate independently to every affected product repository. Its
authoritative `main` commit should normally reference the Linear issue; where a
DDR applies it must reference both IDs. Do not split one issue merely because it
affects several repositories.

Use direct work on `main` when there is no meaningful approval gap:

1. edit on `main` and perform pre-commit diff, syntax, and static checks;
2. commit the scoped result to `main`;
3. perform final governed validation against that committed SHA;
4. record validation evidence outside the product repository, identifying the
   repository, SHA, and governing Linear issue; and
5. push the successfully validated `main` commit to the configured remote.

When work precedes merge acceptance, use a temporary branch containing the issue
ID. Preserve commits and use a merge commit, which is the authoritative
traceability commit. Then validate, evidence, and push the resulting `main` SHA.

Linear `Done` is prohibited until every affected product repository and every
other applicable completion gate passes. Repositories may use different
workflow styles. Push does not prove validation, approval, completion, or
deployment.

Delete a temporary branch only after merge, validation, push, and overall issue
completion. Mandatory pull requests, tags, and branch protection are not
introduced. Work that changes no Git-managed product repository follows existing
controls without an artificial SHA or push.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/git-workflow/1.0.0.md -->

<!-- BEGIN GOVERNANCE SOURCE: 00_Governance/capabilities/ddr/1.0.0.md -->
## DDR capability 1.0.0

A DDR is required only for a significant design decision whose rationale must
outlive immediate Linear and implementation history: material boundary,
interface, architectural-alternative, constraint, dependency, routing,
cross-product, capability, or approved-architecture departure decisions. Routine
implementation, refactoring, bug fixes, wording, diagram layout, and recording
an already-approved design do not normally require one.

If a future maintainer could reasonably ask why this approach was chosen over a
plausible alternative, preserve the answer. Do not create DDRs automatically or
retroactively merely because the capability exists.

Use the approved template at
`01_Governance_Stabilisation/03_DDRs/DDR_Template.md`. There is one global
sequence: `DDR-001`, `DDR-002`, and so on. Filenames contain only the identifier,
for example `DDR-004.md`. Product-specific DDRs normally live under
`<Product>/00_Decisions/`; cross-product DDRs temporarily live in the approved
Governance Stabilisation DDR area.

The registry at `01_Governance_Stabilisation/03_DDRs/DDR_Registry.xlsx` contains
exactly `DDR Number` and `Authoritative File Location`. Reserve the next number
before creating the DDR with location `RESERVED`; never reuse it. Abandoned
reservations become `ABANDONED`. A moved DDR keeps its number and changes only
its location.

Where required, exactly one DDR maps to exactly one Linear issue and conversely;
most issues need none. Split independent significant decisions, not a single
decision affecting several repositories. The Linear issue ID is mandatory.

Every DDR has a mandatory `Supersedes` field containing either the previous DDR
number or `None`. Do not modify an approved DDR to add `Superseded By`. A later
decision uses a new DDR whose `Supersedes` field references the earlier record.

A DDR is editable while its issue is in progress. `Done` requires the completed
record at its registered path, mandatory issue and supersession fields, and its
applicable committed product state. Reserved, abandoned, missing, incomplete, or
applicable uncommitted DDRs fail the gate. It becomes immutable only after
validation, affected-repository Git gates, and Linear `Done`.
<!-- END GOVERNANCE SOURCE: 00_Governance/capabilities/ddr/1.0.0.md -->

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

`ASTV/01_Architecture/ASTV_ARCHITECTURE.md` is the authoritative semantic
architecture record. `ASTV/01_Architecture/ASTV_ARCHITECTURE.drawio` is the
authoritative visual structure and phase-layout record. The live Home Assistant
configuration remains authoritative for deployed entity IDs, inputs, response
variables, service calls, and dependencies.

Governance 1.2.0 must not be activated until the separately authorised ASTV
architecture-normalisation issue has made both asserted paths current and the
Markdown and draw.io authorities agree. This overlay does not authorise that
product rename.

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
