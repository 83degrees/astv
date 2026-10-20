# ASTV-350 Technical Proof Record

## Scope

This record describes the review candidate for ASTV-350. It is repository and
test evidence only. It does not claim production deployment, Beta acceptance or
activation of catalogue state.

The proof covers:

- integration-owned custom-panel and static-route registration;
- an authenticated Home Assistant frontend WebSocket `call_service` envelope
  with `return_response: true` for `SupportsResponse.ONLY` actions;
- response extraction, native error preservation and bounded timeout state;
- read visibility with client affordance gating plus provider-side admin
  enforcement for manage actions;
- capability negotiation and explicit active/draft reads;
- status-first `editable_revision` use and no-retry conflict reconciliation;
- optional AdvNFC reverse lookup with failure isolation;
- digest-addressed frontend asset caching inside the HACS integration tree; and
- responsive layout including narrow viewport and safe-area handling.

The panel itself exposes read-only proof buttons. It intentionally does not
implement the ASTV-351 list/editor workflow or initiate mutation/activation.

## Platform basis

The design is checked against Home Assistant Core 2026.9.4, the supported Core
baseline already recorded by the accepted v1.1.0 contract, and the compatible
Home Assistant 2026.10 panel/WebSocket APIs. The exact 2026.9.4 sources used for
the proof are:

- `panel_custom.async_register_panel`:
  <https://github.com/home-assistant/core/blob/2026.9.4/homeassistant/components/panel_custom/__init__.py>;
- `StaticPathConfig` and `async_register_static_paths`:
  <https://github.com/home-assistant/core/blob/2026.9.4/homeassistant/components/http/server.py>; and
- WebSocket `call_service` handling:
  <https://github.com/home-assistant/core/blob/2026.9.4/homeassistant/components/websocket_api/commands.py>.

Those sources establish that:

- `panel_custom.async_register_panel` accepts a module URL, non-iframe mode,
  `require_admin` and safe-area handling;
- `StaticPathConfig` and `async_register_static_paths` provide the integration
  asset route; and
- WebSocket `call_service` requires `return_response: true` and returns the
  provider payload under `result.response`.

HACS remains governed by
`HOME_ASSISTANT_INTEGRATION_DEPLOYMENT_STANDARD.md`. Frontend assets are ordinary
files under the installed integration directory; no new mechanism is added.
The module content digest changes its registered URL after an update and
restart. Removal cleanup likewise completes through HACS removal and restart,
not config-entry unload.

## Hassfest rework

The first review candidate exposed two Hassfest findings. The manifest keys are
now ordered with `domain` and `name` first and all remaining keys alphabetical.
The `CONFIG_SCHEMA` warning was also applicable: this integration implements
`async_setup` while remaining config-entry-only. It now declares
`cv.config_entry_only_config_schema(DOMAIN)`, explicitly rejecting YAML
configuration without changing its UI/config-entry setup path.

## Reproduction

From the repository root:

```powershell
python -m unittest discover -s 05_Tests -p "test_*.py"
node --test 05_Tests/test_astv_admin_frontend.mjs
python 00_Governance/01_Central/03_Tooling/central_gov_checks.py `
  --repository 83degrees/astv `
  --head codex/astv-350-admin-ui-transport `
  --base beta `
  --beta-exists true `
  --changed-files-file <newline-delimited-changed-files> `
  --repository-root .
```

The Python suite proves registration metadata and preserves the existing ASTV
provider/schema tests. The Node suite exercises the browser adapter without a
live provider: exact WebSocket envelope, error mapping, timeout, non-admin
manage suppression, stale-revision reconciliation without retry, and optional
AdvNFC isolation.

## Runtime proof boundary

No live Home Assistant mutation or production deployment is authorized by
ASTV-350. At the later governed validation/Beta gates, the exact accepted
candidate still requires HACS installation on the authorized target, restart,
panel/sidebar observation, iPhone observation, read/non-admin and admin service
checks, cache-busted upgrade observation and removal/rollback checks required by
the issue and the HACS deployment standard.
