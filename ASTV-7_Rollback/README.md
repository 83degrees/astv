# ASTV-7 rollback snapshots

Created: 2026-08-11

These are exact pre-test copies of the ASTV tag mapping and intent catalogue before any temporary `area_override` value was introduced.

- `starburst/assistive/astv_tag_mapping.yaml`
- `starburst/assistive/astv_intent_catalogue.yaml`

Restore the corresponding source file from this directory, verify its SHA-256 against the values recorded in `ASTV-7_VALIDATION.md`, validate Home Assistant configuration, and reload scripts before retesting.
