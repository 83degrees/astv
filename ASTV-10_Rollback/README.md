# ASTV-10 rollback snapshot

Created: 2026-08-11

The protected package snapshot was copied from current production evidence before staging ASTV-10. Its content preserves the existing `astv_find_uid_record` and endpoint lookup definitions.

To roll back a manual deployment:

1. Restore `starburst/packages/astv/astv_scripts.yaml` from this snapshot.
2. Remove `starburst/assistive/astv_tag_mapping.yaml`.
3. Remove `starburst/assistive/astv_intent_catalogue.yaml`.
4. Validate Home Assistant configuration, then reload scripts or restart as appropriate.

The two new data files have no pre-change snapshots because they did not exist before ASTV-10.
