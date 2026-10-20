# ASTV-351 Implementation Evidence

## Scope and authority

This record describes the review candidate for ASTV-351. It is repository and
automated-test evidence only. It does not claim human acceptance, merge, Beta
integration, deployment, activation or mutation of a live catalogue or draft.

The implementation remains inside the existing
`astv_intent_catalogue` Home Assistant custom panel and uses the accepted
provider adapter. It does not read or write YAML directly, change the provider
contract or schema, introduce another deployable unit, or add the ASTV-352 Tags
or Status workspaces.

## Implemented behavior

- Paginated active and explicit durable-shared-draft list reads.
- Search by canonical intent ID or Name (`title`), supported-type filtering,
  ID/Name sorting, result counts and optional AdvNFC-owned tag counts.
- Explicit active/shared-draft presentation without representing staged data
  as active runtime state.
- Responsive desktop and narrow iPhone/safe-area layouts.
- One full-page General editor for add and edit, with immutable ID after
  creation, required Name, editable supported type, optional area override and
  exact type-specific schema-v1 fields.
- No Description field.
- Client validation followed by the provider's side-effect-free record
  validation before create or update.
- Explicit Save, Cancel and Delete. Save and Delete use guarded staged
  mutations only; activation is not exposed by this issue.
- Browser unload and in-panel navigation warnings for unsaved changes.
- Preserved search, filter, sort and list-scroll state across editor navigation.
- Fresh status `editable_revision` before every guarded mutation. A stale
  result refreshes status and draft state without retry, merge or overwrite.
- A timed-out mutation is presented as indeterminate and reconciled through
  fresh provider reads before another user action.
- Read-only presentation for non-admin users; the provider remains the manage
  authorization boundary.

Tag counts are read-only and failure-isolated. Tag association creation,
editing, removal, delete blocking, deep links, the Status tab and activation
remain ASTV-352 scope.

## Automated evidence

Run from the repository root:

```powershell
node --check custom_components/astv_intent_catalogue/frontend/astv-intent-catalogue-panel.mjs
node --test 05_Tests/test_astv_admin_frontend.mjs
```

The Node suite covers the authenticated response-only WebSocket envelope,
transport errors, bounded timeout, non-admin manage suppression, stale-write
reconciliation without retry, capability-gated draft reads, optional AdvNFC
isolation, provider pagination, schema-v1 client validation, absence of a
Description field, search, filtering and sorting.

Repository Python regressions remain applicable. In the current local sandbox,
the standalone registry proof passed. The full Python suite requires a writable
temporary directory and completes slowly enough that the available command
window did not provide a final result; this is an execution-environment
limitation, not affirmative pass evidence. It must be rerun through the normal
PR checks before review readiness is claimed.

## Review and runtime boundary

Human code review remains required. Responsive visual behavior and authenticated
Home Assistant interaction have not been claimed from repository tests alone.
No merge, HACS Beta tag/install, Home Assistant restart, live draft/catalogue
mutation, activation, `main` promotion or stable release is authorized by this
record.
