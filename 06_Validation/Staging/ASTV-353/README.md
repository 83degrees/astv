# ASTV-353 Disposable Administration UI Stage

This directory defines a private, one-shot Home Assistant stage for the
ASTV administration UI acceptance matrix. The workflow is manual-only and
requires the literal gate value `ASTV-353-G2`; opening or updating a pull
request cannot start the disposable environment. It does not use
`pull_request_target`, repository secrets, or write permissions. Step 1 only
prepares and statically validates these assets. Starting Home Assistant or a
browser remains subject to a separate human-approved Step 2 gate.

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

Pinned fixture SHA-256 identities are checked offline:

- ASTV catalogue: `b00da33486bad0d68673b84d765f0115f14ecd719815fe2bb00f741555f7d7f2`;
- AdvNFC mapping: `79376c93e86e676b062628aa81c618d6c92ad4f7d6af9aba1a635bda592daa7d`;
- inert MediaCat double: `8c2c15931d21556d3381b23697227daf4e3ae0875addcf079407becb05fd1910`.

When separately authorised, `read_only` proves identities, provider/UI loading, admin versus non-admin
controls, desktop/mobile rendering, reverse AdvNFC references, and unchanged
fixture hashes. `controlled_lifecycle` additionally covers Create/Save versus
Activate, edit, delete/reference protection, stale revisions, validation and
MediaCat activation errors, explicit activation, and restoration of the
staging fixture. Controlled lifecycle requires a fresh, separately authorised
manual gate.

Every run captures source trees and hashes, image digests, container/network
isolation, structured API outcomes, desktop/mobile screenshots, logs, fixture
restoration, and disposal status. Containers and the internal network are
removed unconditionally. Any identity, isolation, permission, fixture,
runtime, or restoration mismatch fails the run.
