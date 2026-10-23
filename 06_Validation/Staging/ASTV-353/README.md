# ASTV-353 Disposable Administration UI Stage

This directory defines a private, one-shot Home Assistant stage for the
ASTV administration UI acceptance matrix. Because the workflow does not exist
on the default branch, it uses a GitHub-supported `pull_request` labeled-event
route rather than `workflow_dispatch`. The job is guarded to PR #130, base
`beta`, the exact same-repository head branch, and the label
`ASTV-353-STEP2-READ-ONLY`. Ordinary PR updates cannot start the disposable
environment. Applying that label is reserved for a separate human-approved
Step 2 gate. The route checks out and verifies the immutable PR head and always
sets `read_only`; there is no workflow path to `controlled_lifecycle`. It does
not use `pull_request_target`, repository secrets, or write permissions.

The workflow assembles the stage from immutable product identities:

- ASTV `v0.5.0-beta.c630ce5` / `c630ce5c1ba57cdb4d69b9185adc4a3eed60f7cd`;
- AdvNFC `v1.6.0-beta.dbef2f5` / `dbef2f5133d2efb6f426b348916dc0c58ec1e147`;
- Home Assistant Core `2026.9.4`; and
- Playwright `1.56.1` in the matching versioned browser image.

Home Assistant and the browser share a Docker `--internal` network with no
published ports. The configuration contains only synthetic `astv353_*`
records, one synthetic AdvNFC reverse reference (`A3530001`), a deterministic
MediaCat resolver double, and an inert local sink. It contains no production
configuration, secrets, endpoints, tag UIDs, MQTT listener, or dispatch path.

Before Home Assistant starts, the workflow obtains the actual UID:GID from the
pinned image under the same dropped-capability/no-new-privileges boundary,
assigns the disposable configuration to that identity, rejects any group- or
world-writable path, and proves that the image can create `/config/deps`.
Bootstrap then completes and verifies all Home Assistant onboarding steps before
creating the ASTV config entry through the authenticated Home Assistant REST
config-flow endpoints, followed by the synthetic non-admin identity and browser
session. No unsupported `config_entries/flow/init` WebSocket command remains.
These checks address the bind-mount ownership, incomplete-onboarding, and
config-entry bootstrap findings from the held PR. Browser
output uses a separate directory owned by the pinned browser image's observed
UID:GID; its contents are copied into runner-owned evidence during both the
normal path and unconditional teardown, without a world-writable handoff.
The Playwright packages and copied test/config modules execute together from
`/tmp/pw`, so ESM resolution finds the offline-installed local
`@playwright/test` package rather than resolving the test from `/work`.
Authentication no longer assumes a legacy `/lovelace` redirect: the harness
waits for an authenticated Home Assistant client, fails explicitly on a login
error, and then opens the ASTV panel route with bounded checks. Desktop checks
exercise labelled controls and keyboard focus/navigation without invoking Add,
Save, Delete, or Activate. The non-admin check calls the side-effect-free,
admin-only `validate_intent_record` action and accepts only Home Assistant's
native `unauthorized` rejection.

Pinned fixture SHA-256 identities are checked offline:

- ASTV catalogue: `b00da33486bad0d68673b84d765f0115f14ecd719815fe2bb00f741555f7d7f2`;
- AdvNFC mapping: `79376c93e86e676b062628aa81c618d6c92ad4f7d6af9aba1a635bda592daa7d`;
- inert MediaCat double: `8c2c15931d21556d3381b23697227daf4e3ae0875addcf079407becb05fd1910`.

When separately authorised, the labeled `read_only` route proves identities, provider/UI loading, admin versus non-admin
controls, desktop/mobile rendering, reverse AdvNFC references, and unchanged
fixture hashes. `controlled_lifecycle` additionally covers Create/Save versus
Activate, edit, delete/reference protection, stale revisions, validation and
MediaCat activation errors, explicit activation, and restoration of the
staging fixture. Controlled lifecycle requires a future, separately reviewed
workflow correction and fresh human authorisation; it cannot be selected in
the present workflow.

Every run captures source trees and hashes, image digests, container/network
isolation, structured API outcomes, desktop/mobile screenshots, logs, fixture
restoration, and disposal status. Containers and the internal network are
removed unconditionally. Any identity, isolation, permission, fixture,
runtime, or restoration mismatch fails the run.

Browser failure does not skip integrity evidence. An unconditional post-browser
step records `not_run`, `failed`, or `passed` browser state, compares both
fixture hashes, records read-only restoration as not applicable, and checks
segregation. Browser access is limited to its token-free session file, which is
handed to the observed browser UID:GID as mode 0400 immediately before its
read-only bind mount; the private bootstrap-token inventory remains mode 0600
under the Home Assistant identity. Tracing, automatic screenshots, and video are
disabled; the final teardown redacts every synthetic credential/token byte
sequence from text or binary evidence before upload, records that privacy
result, removes both private session files, and still disposes all resources.
Once bootstrap records the stage as prepared, missing or inaccessible baseline,
fixture, session, or staging-configuration inputs make fixture/segregation
evidence explicitly fail rather than remain `not_run`. Artifact upload has a
separate fail-closed gate after teardown: it requires a successful privacy
manifest, no residual private files, verified disposal, a regular safe evidence
tree, and no trace/video/archive output. Failed, missing, or indeterminate
privacy verification therefore uploads nothing.
