# ASTV-353 Disposable Administration UI Stage

This directory defines a private, one-shot Home Assistant stage for the
ASTV administration UI acceptance matrix. Manual dispatch requires the literal
gate value `ASTV-353-G2`. A separately approved, same-repository PR route is
restricted to PR #128 targeting `beta`, checks out the exact PR head, forces
`read_only`, and cannot enter the controlled lifecycle. It does not use
`pull_request_target`, repository secrets, or write permissions.

The workflow assembles the stage from immutable product identities:

- ASTV `v0.5.0-beta.603e6e1` / `603e6e160b00a357c205b343a950ad64f5a1afae`;
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
creating the ASTV config entry, synthetic non-admin identity, and browser
session. These checks address the failed first smoke's bind-mount ownership
defect and the ordered-path preflight's incomplete-onboarding finding. Browser
output uses a separate directory owned by the pinned browser image's observed
UID:GID; its contents are copied into runner-owned evidence during both the
normal path and unconditional teardown, without a world-writable handoff.

`read_only` proves identities, provider/UI loading, admin versus non-admin
controls, desktop/mobile rendering, reverse AdvNFC references, and unchanged
fixture hashes. `controlled_lifecycle` additionally covers Create/Save versus
Activate, edit, delete/reference protection, stale revisions, validation and
MediaCat activation errors, explicit activation, and restoration of the
staging fixture. The PR route can run only `read_only`; controlled lifecycle
requires a fresh, separately authorised manual gate.

Every run captures source trees and hashes, image digests, container/network
isolation, structured API outcomes, desktop/mobile screenshots, logs, fixture
restoration, and disposal status. Containers and the internal network are
removed unconditionally. Any identity, isolation, permission, fixture,
runtime, or restoration mismatch fails the run.
