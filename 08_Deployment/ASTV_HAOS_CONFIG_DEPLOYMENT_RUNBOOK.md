# ASTV Home Assistant Configuration Deployment Runbook

## Purpose and authority

This runbook applies the approved route:

`haos_config -> operator_selected -> HOME_ASSISTANT_CONFIG_DEPLOYMENT_STANDARD.md`

It is the ASTV-specific deployment map and operational guidance for governed
configuration deployed to the Home Assistant `starburst` instance. The
authorised user or operator selects the practical transport for each
deployment. Manual and tool-assisted methods are both permitted when the
controls below can be satisfied.

This runbook does not itself authorise a deployment. The governing Linear issue,
Central Governance, the Deployment Architecture Standard, the Home Assistant
Configuration Deployment Standard, and the applicable workflow gate remain
authoritative. If this runbook conflicts with a higher authority, stop and use
the higher authority.

## Deployable unit and deterministic path map

ASTV has one `haos_config` deployable unit in this repository. Its current
authoritative source remains under the controlled legacy `04_Source/config/`
location pending a separately governed structure migration. That source root
maps to Home Assistant `/config/`.

| Governed source path | Deterministic `starburst` target path |
| --- | --- |
| `04_Source/config/astv/astv_area_endpoints.yaml` | `/config/astv/astv_area_endpoints.yaml` |
| `04_Source/config/astv/astv_intent_catalogue.yaml` | `/config/astv/astv_intent_catalogue.yaml` |
| `04_Source/config/packages/astv/astv_helpers.yaml` | `/config/packages/astv/astv_helpers.yaml` |
| `04_Source/config/packages/astv/astv_scripts.yaml` | `/config/packages/astv/astv_scripts.yaml` |

Only files included in the accepted candidate and explicitly authorised for the
deployment are transferred. A directory selection, wildcard, editor workspace,
recent-file entry, or unlabeled local copy does not replace the exact source and
target path list in the deployment record.

## Before transfer

The operator records the following in the governing Linear issue or linked
authoritative evidence before changing the target:

1. Deployment authority, authorised operator, and the specific `starburst`
   environment being changed.
2. The accepted repository candidate by exact commit SHA and the exact source
   paths selected from the map above.
3. The matching deterministic `/config/**` target path for every selected
   source file.
4. The operator-selected transport and any material availability, reload,
   restart, or service-impact considerations.
5. The Home Assistant-supported configuration-check route that will validate
   the resulting `starburst` state.
6. The rollback capture location and restoration route for every target path.

The accepted candidate, rather than an uncommitted working tree or moving
branch name, is the source of the payload. Record a source content hash or
equivalent exact-byte identity for each selected file where practical.

Before overwriting, replacing, or removing any target file, capture its
immediate prior bytes to a separate rollback location. Record the target
instance, capture time, original target path, rollback location, and a hash or
other available identity for each capture. Confirm that the complete selected
target set can be restored. Stop if the prior state or a viable recovery route
cannot be established, unless the user gives the specific governed exception
allowed by the Standard after the limitation and consequence are explicit.

## Transfer and resulting-state verification

The authorised operator chooses and records the transport actually used. The
transport can be SMB, a file editor, SCP/SFTP, direct upload, or another manual
or tool-assisted route. This runbook does not prefer or require an operating
system, protocol, Home Assistant App, Git installation on HAOS, GitHub Action,
or agent-accessible Home Assistant endpoint.

Transfer the accepted source bytes directly to the mapped target paths. Do not
edit, reformat, regenerate, normalize line endings, change encoding, or resolve
content differences during transfer. If target-specific transformation is
needed, stop: the transformed payload must first become governed and accepted
source or be handled by separately governed work.

After transfer, establish the resulting target state using the strongest
evidence reasonably available for the chosen transport:

1. Prefer an exact target-side hash or byte-for-byte comparison against the
   accepted source payload.
2. Otherwise record the target read-back or download comparison actually
   performed, supported where useful by file size, complete content inspection,
   or a bounded manifest.
3. State any remaining limitation. A manual copy confirmation or successful
   editor save does not independently bind target bytes to a Git commit.

If the resulting payload cannot be established sufficiently for the governed
change, stop progression. A different operator-selected transport may be used
to retry the same authorised candidate if that resolves the evidence gap
without changing accepted substance.

## Home Assistant configuration validation and Beta entry

Run the Home Assistant-supported configuration check on `starburst` after the
transfer and against the resulting target state. Record the route used, time,
result, material warnings or errors, and the evidence binding that result to the
deployed state.

A file transfer, YAML parse, editor save, restart attempt, or absence of an
immediate visible fault does not replace the Home Assistant configuration
check. Do not reload or restart Home Assistant until the configuration check
succeeds and the applicable action is authorised.

For a runtime candidate following `WF-01`, the reviewed issue change targets the
persistent `beta` branch. Record the exact post-integration Beta commit SHA.
Agent-assisted deployment requires the explicit deployment authorisation
applicable at the Beta-entry gate. The issue may enter `Beta` only after the
exact candidate is deployed, resulting identity is sufficiently established,
and the Home Assistant configuration check passes. Beta operation and the
remaining completion controls are still required; configuration validation
alone is not Beta acceptance.

## Fail-closed and rollback procedure

Stop deployment or Beta progression when authority, source candidate, source
path, target instance, target path, prior-state capture, resulting payload
identity, Home Assistant validation, or required evidence is missing,
ambiguous, failed, or contradictory. Preserve the evidence already obtained
and do not describe the candidate as deployed, validated, or accepted.

When rollback is required:

1. Record the failure that triggered rollback and obtain any action-specific
   authority required to restore the target.
2. Restore every affected deterministic target path from its recorded immediate
   prior-state capture using an available operator-selected transport.
3. Verify the restored target state with the strongest evidence reasonably
   available.
4. Repeat the Home Assistant-supported configuration check against the restored
   `starburst` state.
5. Record restored paths, prior-state identity, transport, validation result,
   final target status, and any unresolved recovery condition.

If restoration or post-rollback validation cannot be completed and verified,
surface the unresolved target state promptly and keep the issue incomplete.

## Deployment evidence record

Copy this checklist into the governing Linear issue or linked authoritative
evidence and complete it for each deployment. Do not record credentials,
tokens, backup keys, or other secrets.

```text
ASTV deployment authority / governing issue:
Authorised operator:
Authorisation reference and time:

Source repository: 83degrees/astv
Accepted candidate commit SHA:
Persistent beta commit SHA (WF-01):
Selected source paths and source byte identities:

Target instance: starburst
Target environment:
Exact target paths:
Operator-selected transport actually used:
Deployment time:

Immediate prior-state capture time:
Prior-state paths, identities, and rollback locations:
Rollback route confirmed:

Target read-back / comparison / hash evidence:
Remaining provenance limitation, if any:

Home Assistant configuration-check route:
Configuration-check time and result:
Material warnings or errors:
Reload or restart authority and result, if applicable:

Overall deployment outcome:
Beta-entry evidence reference, if applicable:
Rollback invoked: yes / no
Rollback and revalidation result, if invoked:
Unresolved conditions:
```
