# ASTV-76 validation

## Result

ASTV-76 retired the dormant catalogue-reference v1 branch from
`script.astv_adapter_advmedia`. The deployed adapter accepts only the normalized
MediaCat record, ASTV-selected execution method, ASTV-selected media player, and
optional profile override. It calls `script.advmedia_process_media_record`
exactly once and returns only its `playback_payload` as the existing ASTV
`payload_response`.

## Pickup and authority

- Linear issue: `ASTV-76`
- Team/project: `astv` / `ASTV`
- Pickup: `Ready` to `In Progress` on 2026-08-25
- Dependency: `ASTV-65` was `Done`, with its operational rollback window
  explicitly closed before pickup.
- Production mutation authority: replace only
  `script.astv_adapter_advmedia` through the Home Assistant configuration API;
  no restart was planned or performed.

## Caller inventory

Fresh Home Assistant configuration-body search found two configured callers:

| Caller | Current role |
| --- | --- |
| `script.astv_ha_mplayer_engine` | Current normalized caller; passes `media_record`, `selected_execution_method`, and `media_player`. |
| `script.astv_handle_provider` | Retained dormant legacy branch; still supplies the old catalogue-reference shape but is not selected by current normalized media records. |

The search also returned the adapter itself by name. No automation caller was
found. The live search reported partial coverage because three YAML-defined
automations and three YAML-defined scripts are not exposed by the per-item
configuration endpoint. The read-only `Production_ReadOnly/starburst/scripts.yaml`
snapshot contains one caller, `script.astv_handle_provider`; no other snapshot
definition calls the adapter. The snapshot has no capture manifest and is not
fresh production proof, so this result is recorded as supplementary evidence,
not an exhaustive live guarantee.

After deployment, fresh searchable live configuration contained no ASTV call to
`script.advmedia_prepare_playback`. That entity remains present only by its own
AdvMedia-owned standalone definition pending ASTV-67.

## Source, rollback, and deployment

| Artifact | SHA-256 / live hash |
| --- | --- |
| `ASTV-76_Source/astv_adapter_advmedia.json` | `cc949ce7e2192f8ee06ee5c5f3c7c8bd0e50ae012abc88d20595c85b95cbb1dc` |
| `ASTV-76_Rollback/astv_adapter_advmedia.pre-change.json` | `848e4ec3dd5ac22a164090e7b0a3e0cb8799db50f6958ca685b9dee16057773d` |
| `ASTV-76_Rollback/README.md` | `a21b7074994f0d49db9621cdbb84fa167355d6e0453e1f1c7aea4ec6d12ec457` |
| Live pre-change configuration | `fe00d0cea795cc06` |
| Live installed configuration | `f3cd9fa7b196ccce` |

The rollback JSON was compared structurally with a fresh live read before
deployment: script body, category `01KY5BCDDWE2CK0HM5RT0KXTNX`, and configuration
hash all matched. The target was JSON-parsed and structurally audited before
deployment: exactly four fields, exactly one core call, exactly one payload
extraction, and no v1 field, branch, shape-detection, or prepare-playback token.
Home Assistant template evaluation preserved a complete record with an unknown
additive field and the selected execution context.

Deployment used optimistic locking against `fe00d0cea795cc06`. The API returned
success; a fresh read was structurally identical to the repository target and
reported installed hash `f3cd9fa7b196ccce`. No restart or reload occurred.

## Normal-entry runtime proof

The first BBC Radio 2 request reached the correct terminal playback call, but
the kitchen speaker became unavailable and logged a contemporaneous
`pychromecast.socket_client` connection failure. The user heard only the Cast
wake chime. This was not counted as acceptance proof.

After the speaker reconnected, Classic FM UID `7AB06354E000` ran through the
normal `script.astv_uid_gateway` path with trigger entity
`sensor.pi_nfc_99_last_uid`:

| Component | Trace run ID |
| --- | --- |
| UID Gateway | `af667072d2ba9d3837d761f594dcf9c5` |
| Media Intent Engine | `1f0ef7929fb7db3689f792bbc7add1af` |
| HA Media Player Engine | `35ce8ac1d0801e40d57023468dceed47` |
| ASTV AdvMedia Adapter | `cb32ad3545e9032bfc7cbe7fe13ebfef` |
| AdvMedia processing core | `a57fd4331da493ef55a205a5b18ea6d2` |

All traces were `stopped` / `finished`. The request performed one normalized
MediaCat lookup, selected `ha_mplayer` and
`media_player.kitchen_speaker`, called the adapter and core once, preserved the
complete record and selected context, mapped only `playback_payload` into the
HA Media Player engine, and issued one `media_player.play_media` action. The
speaker entered `playing` with title `Classic FM`; the user explicitly confirmed
audible playback. No related error was recorded for the successful run.

## Contract and documentation

`contracts/ASTV_ADVMEDIA_INTERFACE.md` was corrected in two stages: before the
runtime change it described v2 as current and the configured v1 adapter branch
as the approved ASTV-76 removal target; after successful proof it was promoted
to the v2-only ASTV boundary. The retained AdvMedia catalogue-reference entry is
labelled as a separate standalone interface pending ASTV-67.

`ASTV/01_Architecture/ASTV_ARCHITECTURE.md` and `ASTV/CURRENT_STATE.md` describe
the proven v2-only adapter. The manual Draw.io file remains an explicitly
historical pre-cutover visual and was not changed.

Final documentation hashes:

| File | SHA-256 |
| --- | --- |
| `contracts/ASTV_ADVMEDIA_INTERFACE.md` | `ad078f26c6e6b311f193e08b6423002b7e884e2051933d912d96d5e7c816c23c` |
| `ASTV/01_Architecture/ASTV_ARCHITECTURE.md` | `b0be0c767e7d0f9403ef6a7ddf4df7f04a798ab9e01aca5c4079279be88281ff` |
| `ASTV/CURRENT_STATE.md` | `8fd46730c7b9bc493d8b1df033ca2676ca75329bfa5b74ecc17690200eb923bf` |

The central `astv-advmedia` registry entry remained version `2.0.0`, status
`current`, path `contracts/ASTV_ADVMEDIA_INTERFACE.md`, with validation timestamp
`2026-08-24T20:09:37.490Z`. Its unchanged registry file SHA-256 is
`dc2a6a838146e207cb4d2f49fb15cef2078b4c412d4dd0af47bf81a42955b98f`.
Governance files were not changed.

## Limitations

- Live caller search is partial for the six YAML-defined items described above;
  the static read-only snapshot supplements but does not eliminate that limit.
- The retained `script.astv_handle_provider` legacy AdvMedia branch is a dormant
  configured caller with the retired input shape. Current normalized records do
  not select it; changing or removing that upstream legacy path was not in
  ASTV-76 scope.
- Audible confirmation is a human observation, not continuous monitoring.
- The initial BBC Radio 2 Cast transport failure is retained as evidence; no
  ASTV, AdvMedia, MediaCat, endpoint, or network configuration was changed to
  conceal it.
