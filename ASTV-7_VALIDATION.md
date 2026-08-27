# ASTV-7 validation evidence

Date: 2026-08-11

Kitchen area ID: `5fa17a3cccaf4af0a5daef18141375fd`

Kitchen NFC reader: `sensor.pi_nfc_99_last_uid`

Controlled Classic FM tag: `7AB06354E000`

## Rollback and restoration

Verified pre-test snapshots exist in `ASTV-7_Rollback`.

| Data file | Pre-test and final SHA-256 |
| --- | --- |
| `astv_tag_mapping.yaml` | `44A4180F84D0ACC7477B2CA7BD4B45CA08585BA9DBEDBA5BA971E5EB0211BEBD` |
| `astv_intent_catalogue.yaml` | `8B99B82A4D2E5C47F787A1393B844486086F726C12B4CEFC9EB48B71181ECBD2` |

After testing, the live Home Assistant files, writable source files, and rollback snapshots matched these hashes. Neither file retains an `area_override`. Home Assistant configuration validation passed before each reload and after final restoration.

## Direct Resolve Area checks

Only `script.astv_resolve_area` was called for marker tests. The markers were never written to either data file or passed to Intent Gateway or any downstream component.

| Check | Expected `target_area` | Actual `target_area` | Result |
| --- | --- | --- | --- |
| Trigger and intent markers supplied | `ASTV7_TRIGGER_MARKER` | `ASTV7_TRIGGER_MARKER` | Pass |
| Intent marker and Kitchen reader supplied | `ASTV7_INTENT_MARKER` | `ASTV7_INTENT_MARKER` | Pass |
| No overrides and Kitchen reader supplied | `5fa17a3cccaf4af0a5daef18141375fd` | `5fa17a3cccaf4af0a5daef18141375fd` | Pass |
| No sources supplied | empty | empty | Pass |

These calls prove `trigger_area_override -> intent_area_override -> area_id(trigger_entity) -> unresolved`.

## Unresolved Intent Gateway check

Direct Intent Gateway trace `8f0d40ed5c24767531e99398b7c0fdad` used known `intent_id: classic_fm` with blank overrides and no trigger entity.

- Expected `target_area`: empty.
- Actual `target_area`: empty.
- Persistent notification: `No Target Area Resolved`, naming `classic_fm`.
- The trace stopped in the unresolved branch before `script.astv_select_intent_engine`.

## Kitchen-only end-to-end checks

Every executing call used `sensor.pi_nfc_99_last_uid` and targeted only `media_player.kitchen_speaker` through Kitchen area ID `5fa17a3cccaf4af0a5daef18141375fd`.

| Check | UID Gateway trace | Intent Gateway trace | Resolve Area inputs | Expected / actual target |
| --- | --- | --- | --- | --- |
| Baseline, no overrides | `a4d7891be38702c47d3267efae44a77c` | `4f4705ef15c733de8086cb71e4b8a645` | both overrides blank; Kitchen reader | Kitchen / Kitchen |
| Temporary intent-catalogue override | `4dee8194d3a0590cd1ad6dabeffd761a` | `c2b1fdf8c0e3840f9a4fcc8a15c83a51` | trigger blank; `intent_area_override` = Kitchen; Kitchen reader | Kitchen / Kitchen |
| Temporary tag-mapping override | `27684cef5aef72270a939338532220a0` | `3bea9641474a3dd76b13809829f76bcd` | `trigger_area_override` = Kitchen; intent blank; Kitchen reader | Kitchen / Kitchen |

For the intent override, Resolve Area child trace `5279ec4b92a0481d454a8960e50937ea` returned Kitchen. For the tag override, Resolve Area child trace `a4b15e371906fda305f4491e9e4ada7a` returned Kitchen.

The catalogue override was restored and scripts reloaded before the tag override was introduced. The tag override was restored immediately after its test. No both-overrides executing test was needed because the isolated marker test already proved precedence with distinct values.

## Final state

- No production override remains.
- No test marker is stored in production data.
- Both live data files exactly match the verified pre-test snapshots.
- Final Home Assistant configuration check is valid and scripts reloaded successfully.
- Existing non-test mapping and catalogue records remain unchanged.
- No non-Kitchen execution occurred.
