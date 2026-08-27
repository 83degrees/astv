# ASTV-12 validation evidence

Date: 2026-08-11

## Production cutover

- `script.astv_uid_gateway` was read before mutation at configuration hash `bef76d1a1a449709`.
- Exact recoverable snapshot: `ASTV-12_Rollback/astv_uid_gateway.pre-cutover.json`.
- The cutover configuration was re-read from live Home Assistant at hash `bbb9524c16958be9`.
- UID Gateway now calls `script.astv_find_tag_record`, captures `tag_record_response`, validates a non-blank `intent_id`, creates the temporary `Tag Record Found` diagnostic, and calls only `script.astv_intent_gateway` for subsequent ASTV processing.
- The tag record's optional `area_override` is passed as Intent Gateway's `trigger_area_override`; all initial records were confirmed to omit it.
- The missing/blank `intent_id` guard is present in the live script logic. No malformed production record was introduced or executed.

## Static and lookup checks

- Tag mapping: nine records.
- Intent catalogue: eight records.
- Every mapping has a non-blank `intent_id` that names a catalogue record.
- Both `7AB06354E000` and `E38B36C82A81` map to the single `classic_fm` catalogue record.
- No tag mapping or catalogue record contains `area_override`.
- Direct Find Tag Record lookup normalized `7ab06354e000` and returned `intent_id: classic_fm`.
- Unknown tag `ASTV12_UNKNOWN` returned `{}`.
- Direct Find Intent Record lookup normalized `CLASSIC_FM` and returned the Classic FM catalogue record.
- Unknown intent `astv12_unknown` returned `{}`.

## Safe-stop validation

- Unknown UID Gateway trace: `2cd7d307f8cc00158a02f0d9aeed28dd`.
- Find Tag Record returned `{}`.
- Persistent notification title was `No Tag Record Found` and included `ASTV12_UNKNOWN_UID`.
- The trace stopped before Intent Gateway.

## Kitchen-only end-to-end validation

Every executing call supplied `sensor.pi_nfc_99_last_uid`. Every nested Intent Gateway trace resolved `target_area` to Kitchen area ID `5fa17a3cccaf4af0a5daef18141375fd`. Both area override inputs were blank. Select Intent Engine received only `request` and `target_area`; `trigger_entity` was not present after Resolve Area. No non-Kitchen executing test occurred.

| UID | Intent | UID Gateway trace | Intent Gateway trace | Proven route and terminal action |
| --- | --- | --- | --- | --- |
| `7AB06354E000` | `classic_fm` | `c09dfdbbe0525a8d33e3535f643bd596` | `5bbc3fa3ce5c19fbc6b5187a05232bdf` | Radio Browser → HA Media Player → `media_player.play_media` on `media_player.kitchen_speaker` |
| `DEADBEEF` | `bbc_radio_2` | `58fd93c9d486133a5e9d523c4917d630` | `fd90a4e0d9010a51efde7a23c1279874` | AdvMedia → HA Media Player → `media_player.play_media` on `media_player.kitchen_speaker` |
| `DEADSMOOTH` | `smooth_radio` | `b8779e8b7bbbaff768fb5e0b5991efe4` | `e807297809e7ecef6ac59a410d49a40e` | Google Home Device → Google Assist → `google_assistant_sdk.send_text_command` |
| `DEADMORNING` | `morning_routine` | `48b21bfd2428fa855505685824b26b6a` | `2b11c66b378997ff30278d91b33385eb` | Routine → Google Automation Engine → `input_boolean.gh_trigger_101` turned on |

Each successful UID trace recorded a `Tag Record Found` notification containing UID, `sensor.pi_nfc_99_last_uid`, resolved intent ID, and `Area Override: (none)`.

## Unchanged boundaries and rollback

- `automation.astv_tag_listener` retained configuration hash `61119957b4715369` and its two reader sensors.
- `script.astv_find_uid_record` remains available in live Home Assistant.
- `Production_ReadOnly/starburst/assistive/astv_tags2.yaml` retained SHA-256 `C348EEF1FC1E19796CEB2695941C536436951C158EC3E24E0F5F951819ED3563`.
- `starburst/packages/astv/astv_scripts.yaml` retained SHA-256 `871B6B8F7F3B292721E284C16407B3909420A7E085E7BECC7541000471220504`.
- Rollback can restore the exact pre-cutover UID Gateway through the normal Home Assistant script configuration API without recreating it from memory.

## Architecture evidence

- The user confirmed the active diagram was closed before Codex read and edited it.
- Exact pre-cutover archive: `01_Architecture/Archive/ASTV_Architecture_pre_ASTV-12_2026-08-11.drawio`.
- Pre-cutover diagram and archive SHA-256: `4E5FAD48892318E22BF73B4488F3B8F0F7738C3BC82EB0100E1C09E82BE83662`.
- Active diagram SHA-256 after the smallest required cutover edits: `46D484A848743ADC0098BFF05E431B97A63D6A5BC8ABE6696285383CCD30509A`.
- XML validation found 188 cells and zero dangling `parent`, `source`, or `target` references.
- The active diagram now shows UID Gateway calling Find Tag Record, receiving `tag_record_response`, and invoking Intent Gateway with separate `intent_id`, `trigger_area_override`, and `trigger_entity` connector labels.
- The obsolete UID Gateway → Resolve Area and UID Gateway → Select Intent Engine connectors are absent.
- Find Tag Record is connected to `astv_tag_mapping.yaml`; the legacy lookup and `astv_tags2.yaml` are shown as retained rollback components with no active execution connector.
- No PNG or PDF was exported.
