# ASTV-353 Disposable Administration UI Stage

This directory defines a private, one-shot Home Assistant stage for the
ASTV administration UI acceptance matrix. It is deliberately manual-dispatch
only and requires the literal gate value `ASTV-353-G2`; this G1 change does not
authorize dispatching it.

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

`read_only` proves identities, provider/UI loading, admin versus non-admin
controls, desktop/mobile rendering, reverse AdvNFC references, and unchanged
fixture hashes. `controlled_lifecycle` additionally covers Create/Save versus
Activate, edit, delete/reference protection, stale revisions, validation and
MediaCat activation errors, explicit activation, and restoration of the
staging fixture. A fresh human gate is required before either mode is run.

Every run captures source trees and hashes, image digests, container/network
isolation, structured API outcomes, desktop/mobile screenshots, logs, fixture
restoration, and disposal status. Containers and the internal network are
removed unconditionally. Any identity, isolation, permission, fixture,
runtime, or restoration mismatch fails the run.
