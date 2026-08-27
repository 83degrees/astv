# ASTV-64 Rollback

This package preserves the complete legacy eight-record ASTV intent catalogue
captured for ASTV-64. It is inactive rollback material for the coordinated
ASTV-65 cutover and must remain available until the user explicitly closes the
rollback window.

## Preserved source

- Production target: `/config/assistive/astv_intent_catalogue.yaml`
- Read-only capture source:
  `Production_ReadOnly/starburst/assistive/astv_intent_catalogue.yaml`
- Package copy:
  `starburst/assistive/astv_intent_catalogue.yaml`
- Expected SHA-256:
  `8b99b82a4d2e5c47f787a1393b844486086f726c12b4cefc9eb48b71181ecbd2`

The package copy is byte-for-byte identical to the read-only source. Recovery
does not depend on Git history.

## Restoration procedure

ASTV-65 owns any production rollback. Do not run this procedure as part of
ASTV-64.

1. Pause new ASTV media requests for the coordinated recovery window.
2. Hash the current `/config/assistive/astv_intent_catalogue.yaml` and compare
   it with the prepared-catalogue hash recorded in `ASTV-64_VALIDATION.md`. Stop
   and investigate if it differs unexpectedly.
3. Replace only `/config/assistive/astv_intent_catalogue.yaml` with the complete
   package copy at
   `ASTV-64_Rollback/starburst/assistive/astv_intent_catalogue.yaml`.
4. Confirm the restored file SHA-256 is
   `8b99b82a4d2e5c47f787a1393b844486086f726c12b4cefc9eb48b71181ecbd2`.
5. Run Home Assistant configuration validation.
6. Reload scripts only so the `!include` used by
   `script.astv_find_intent_record` is re-read. Do not restart Home Assistant
   unless the script reload fails and the user separately authorizes a restart.
7. Re-read all eight intent records. Confirm all seven media records contain
   their original `params.sources` mappings and `morning_routine` is unchanged.
8. Complete the coordinated MediaCat and AdvMedia rollback required by ASTV-65
   before resuming ASTV media requests; the restored legacy ASTV records must
   not be left active against an incompatible MediaCat/AdvMedia activation set.

The restoration unit is the whole file. Do not restore or activate individual
records as a supported mixed state.
