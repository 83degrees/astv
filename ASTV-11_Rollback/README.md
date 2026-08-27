# ASTV-11 rollback snapshot

Created: 2026-08-11

Before the production mutation, live Home Assistant confirmed that `script.astv_intent_gateway` did not exist. The existing ASTV-9/10 entities and the legacy UID Gateway were read and left unchanged.

The protected package snapshot in this directory verifies that the ASTV lookup package remained unchanged. Intent Gateway was created through Home Assistant's normal script configuration API because it contains no protected `!include` data source.

To roll back ASTV-11:

1. Remove only `script.astv_intent_gateway` from production through Home Assistant's script configuration API.
2. Confirm the protected ASTV package still matches the snapshot in this directory.
3. Validate the unchanged legacy UID path.

No existing production script is replaced by this issue.
