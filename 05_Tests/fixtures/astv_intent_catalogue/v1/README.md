# ASTV Intent Catalogue schema-v1 fixtures

These fixtures support the proposed
`03_Contracts/ASTV_INTENT_CATALOGUE_SCHEMA.md`. They are documentation
evidence, not deployed configuration and not executable validator code.

| Fixture | Expected schema-v1 result | Purpose |
| --- | --- | --- |
| `legacy/current_baseline_unversioned.yaml` | Invalid as v1 | Exact eight-record pre-migration bytes retained for semantic-equality and paired-rollback evidence |
| `valid/current_baseline_migrated.yaml` | Valid | Exact eight-record migration candidate |
| `valid/area_override.yaml` | Valid | Optional record-level area override on both record types |
| `valid/well_formed_missing_mediacat_target.yaml` | Structurally valid | Well-formed reference; target existence belongs to MediaCat |
| `invalid/missing_media_reference.yaml` | Invalid | Required `item_id` absent |
| `invalid/invalid_media_reference.yaml` | Invalid | MediaCat identifier violates its provider-owned pattern |
| `invalid/unknown_intent.yaml` | Invalid | Unsupported intent discriminator |
| `invalid/unknown_field.yaml` | Invalid | Strict unknown-key policy |
| `invalid/malformed_routine.yaml` | Invalid | Required `routine` absent and `params` non-empty |
| `invalid/duplicate_normalized_ids.yaml` | Invalid | Distinct YAML keys collide after trim/lower normalization |
| `invalid/unsupported_schema_version.yaml` | Invalid | Current-version-only rejection |
| `invalid/scalar_constraints.yaml` | Invalid | Blank, null and wrong-type values |
| `invalid/rollback_legacy_unversioned.yaml` | Invalid as v1 | Reduced representative legacy recovery input; no implicit migration |

A temporarily unavailable MediaCat provider does not change static schema
validity. The well-formed missing-target fixture is therefore also suitable for
testing future `dependency_unavailable` handling by replacing the provider
state, not the fixture. Activation/probing behavior belongs to ASTV-332.
