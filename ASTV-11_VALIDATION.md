# ASTV-11 validation evidence

Date: 2026-08-11

## Production contract

- Created `script.astv_intent_gateway` with friendly name `ASTV - Intent Gateway`.
- Fields are exactly `intent_id`, optional `trigger_area_override`, and optional `trigger_entity`.
- The script has no response object.
- Live configuration hash after creation: `5d1280fa773b54fe`.
- `sensor.pi_nfc_99_last_uid` resolves through Home Assistant to area ID `5fa17a3cccaf4af0a5daef18141375fd`, area name `Kitchen`.

## Safe-stop validation

- Unknown intent trace: `79f80a55b9e67cfa8e6191d171297b8f`.
  - `script.astv_find_intent_record` returned `{}`.
  - Persistent notification title was `No Intent Record Found` and included `astv_11_unknown_intent`.
  - The trace stopped before Resolve Area and Select Intent Engine.
- Unresolved-area trace: `c9744848a8f0fe6c0a3bbb7d8c7ead03`.
  - `classic_fm` resolved successfully.
  - Resolve Area returned an empty `target_area` when no trigger entity or override was supplied.
  - Persistent notification title was `No Target Area Resolved` and identified `classic_fm`.
  - The trace stopped before Select Intent Engine.

## Kitchen-only route validation

Every executing call supplied only `sensor.pi_nfc_99_last_uid` as the area source. Every gateway trace resolved `target_area` to Kitchen area ID `5fa17a3cccaf4af0a5daef18141375fd`. No non-Kitchen executing test was performed.

| Intent | Gateway trace | Proven route and terminal action |
| --- | --- | --- |
| `classic_fm` | `b345a17e7af52a960e227792aa1a820b` | Media → HA Media Player → Radio Browser → `media_player.play_media` on `media_player.kitchen_speaker` |
| `bbc_radio_2` | `d67e83c4fd64bc128f28b4e0ccf5eccb` | Media → HA Media Player → AdvMedia → `media_player.play_media` on `media_player.kitchen_speaker` |
| `smooth_radio` | `a871760caa75116ce1ee5a66a2b34d41` | Media → Google Home Device → Google Assist → `google_assistant_sdk.send_text_command` with `Play Smooth Radio on Global Player on Kitchen Speaker` |
| `morning_routine` | `de715bbd6be9435ffb0b1f6391b33df8` | Routine → Google Automation Engine → resolved `input_boolean.gh_trigger_101` → `input_boolean.turn_on` |

The gateway traces show that Select Intent Engine received only `request` and `target_area`. `intent_id`, `trigger_area_override`, and `trigger_entity` were not present in its service data.

## Legacy-path regression evidence

- `automation.astv_tag_listener` remained enabled and was not changed.
- `script.astv_uid_gateway` remained available and was not changed; configuration hash before and after ASTV-11 was `bef76d1a1a449709`.
- `script.astv_select_intent_engine` remained unchanged; configuration hash before and after ASTV-11 was `b61a25f53d8c67a2`.
- `script.astv_find_uid_record`, `astv_tags2.yaml`, Tag Listener, and the UID Gateway were not mutated or invoked by the ASTV-11 executing tests.

## Rollback and architecture evidence

- Pre-change package snapshot: `ASTV-11_Rollback/starburst/packages/astv/astv_scripts.yaml`.
- Pre-change package SHA-256: `871B6B8F7F3B292721E284C16407B3909420A7E085E7BECC7541000471220504`.
- Pre-change diagram archive: `01_Architecture/Archive/ASTV_Architecture_pre_ASTV-11_2026-08-11.drawio`.
- Active and archived diagram hashes matched before editing: `AB7558B92F3ED92156F9192E1D5E2D1103A9992214B282A26BCAE38EA5113702`.
- Updated active diagram SHA-256: `4E5FAD48892318E22BF73B4488F3B8F0F7738C3BC82EB0100E1C09E82BE83662`.
- The updated draw.io file parses as XML. No PNG or PDF export was created.
