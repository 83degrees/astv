# ASTV-13 validation evidence

Date: 2026-08-11

## Pickup gates and source verification

- ASTV-12 was verified `Done` before pickup.
- The user's explicit retirement approval is recorded in the ASTV-13 Linear comment dated 2026-08-11.
- ASTV-13 was `Ready` and was moved to `In Progress` before implementation.
- The live Home Assistant source was located through the Samba `config` share at `/config`.
- Before removal, an exhaustive live YAML/JSON scan found `script.astv_find_uid_record` and `astv_tags2.yaml` only in `/config/packages/astv/astv_scripts.yaml`: the script definition and its own include. No automation or other script called it.
- Live UID Gateway evidence and ASTV-12 validation took precedence over the stale `Production_ReadOnly/starburst/scripts.yaml` reference, which still shows the pre-cutover path.
- Contracts contained no legacy references.

## Recovery evidence

- Full Home Assistant backup: `172b43b6` (`ASTV-13_pre_retirement_2026-08-11`).
- Backup completed successfully before production mutation.
- Final backup listing confirmed `172b43b6` remains present and protected, includes Home Assistant configuration, and was created against Home Assistant `2026.7.4`.
- Exact pre-retirement live hashes:
  - `/config/packages/astv/astv_scripts.yaml`: `871B6B8F7F3B292721E284C16407B3909420A7E085E7BECC7541000471220504`
  - `/config/assistive/astv_tags2.yaml`: `C348EEF1FC1E19796CEB2695941C536436951C158EC3E24E0F5F951819ED3563`
- Human-readable component snapshots and restoration steps are recorded under `ASTV-13_Rollback/`.
- The full Home Assistant backup is the byte-exact recovery source.

## Retirement and configuration validation

- Removed only `astv_find_uid_record` and its exclusive `astv_tags2.yaml` include block from the live and staged ASTV package.
- Final live and staged package SHA-256 values match at `5EDB053F79FBD299730D45AC8AC7C29A84456AF718159B18136ECD2A565FF5D9`.
- Home Assistant configuration validation passed after the package edit while the legacy data file still existed.
- Removed only `/config/assistive/astv_tags2.yaml` after the include was gone.
- Home Assistant configuration validation passed again after data removal.
- Scripts reloaded successfully; no restart occurred.
- Removed the now-stale `script.astv_find_uid_record` entity-registry entry after its YAML source was gone.
- `script.astv_find_tag_record`, `script.astv_find_intent_record`, `script.astv_uid_gateway`, and `script.astv_intent_gateway` remained available.
- The final exhaustive live YAML/JSON scan returned no `astv_find_uid_record` or `astv_tags2.yaml` references.

## Mapping and catalogue validation

- All nine active UIDs resolved through `script.astv_find_tag_record` to their expected intent IDs.
- Both Classic FM UIDs resolved to `classic_fm`.
- All eight referenced intent IDs resolved through `script.astv_find_intent_record` to non-empty records.
- Seven records resolved to `media.play_source`; `morning_routine` resolved to `routine.run`.

## Kitchen-only regression evidence

Both executing regressions supplied `sensor.pi_nfc_99_last_uid`. Intent Gateway resolved area ID `5fa17a3cccaf4af0a5daef18141375fd`, verified as Kitchen. No non-Kitchen executing test occurred.

| UID | UID Gateway trace | Intent Gateway trace | Result |
| --- | --- | --- | --- |
| `7AB06354E000` | `d4110d9101fe840a9f64055f5d5faf77` | `11e3a2ea991cea14fc0d2ac82330fc82` | Find Tag Record -> `classic_fm` -> Find Intent Record -> Kitchen -> Radio Browser -> HA Media Player -> Classic FM on `media_player.kitchen_speaker` |
| `DEADMORNING` | `8fa9eed1377fba8c1a168289a57a4afe` | `36bc75bc3cf2801fb45aecbd5e346fae` | Find Tag Record -> `morning_routine` -> Find Intent Record -> Kitchen -> Routine -> Google Automation Engine -> `input_boolean.gh_trigger_101` on |

Both UID Gateway traces completed with state `stopped` and execution `finished`. Neither trace called the retired lookup.

## Architecture and archive evidence

- The user confirmed the active diagram was closed before Codex read and edited it.
- Exact pre-change archive: `01_Architecture/Archive/ASTV_Architecture_pre_ASTV-13_2026-08-11.drawio`.
- The pre-change active diagram SHA-256 was `B7003D3E0C5E53481B4053DB3E10DF0AD7BB7990C8BD333532B750442C2AD3DB`.
- Removed only the obsolete `astv-retained-legacy-uid` object from the active diagram.
- The post-change active diagram SHA-256 is `A6A56C33EDAF105C33CD65DDFEFCCC0EB77F7EE04749CAA255551C8B99DC4411`.
- XML validation found 187 cells, zero dangling `parent`, `source`, or `target` references, and no `astv-retained-legacy-uid` object.
- Removed only transitional legacy-retention text and the retired data dependency from `ASTV_ARCHITECTURE.md`.
- Prior archives were not modified or deleted. No PNG or PDF was exported.
