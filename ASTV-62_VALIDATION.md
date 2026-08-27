# ASTV-62 Validation

## Result

ASTV-62 installed the inactive HA Media Player consumer and dual-shape AdvMedia
adapter in live Home Assistant. The current legacy Radio Browser and AdvMedia
paths passed normal-entry regression testing. The normalized v2 path was proved
by non-live template/composition and installed-structure checks only because
`script.advmedia_process_media_record` is not deployed. No record activation,
AdvMedia deployment, MediaCat deployment, provider, dispatcher, intent data, or
endpoint data was changed.

## Authorization and source checks

- Linear issue `ASTV-62` was retrieved from team `astv` in `Ready`; all listed
  dependencies were `Done`.
- The issue was checked against generated governance, current live read-only
  evidence, `01_Architecture/ASTV_ARCHITECTURE.md`, and
  `contracts/ASTV_ADVMEDIA_INTERFACE.md`, then moved to `In Progress` before
  mutation.
- `CURRENT_WORK.md` contained only its template and did not override Linear.
- The 2026-08-12 production snapshot had no capture manifest and was stale for
  this change. It was treated as limited read-only evidence and supplemented by
  fresh live configuration reads.
- Live caller search was partial: three YAML-defined automations and three
  YAML-defined scripts were not retrievable through the storage configuration
  API. Known callers were confirmed from live definitions and retained
  architecture evidence.

## Pre-change evidence and rollback

| Script | Pre-change hash | Category |
| --- | --- | --- |
| `script.astv_adapter_advmedia` | `1ddc07631782c3a4` | `01KY5BCDDWE2CK0HM5RT0KXTNX` (`ASTV (Providers)`) |
| `script.astv_ha_mplayer_engine` | `62a363022c26ca89` | `01K9QMV1C04YWV4HAS8G6V7FRV` (`Assistive Tech`) |

The exact definitions were captured before mutation as one coordinated rollback
unit in `ASTV-62_Rollback/`. File SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `astv_adapter_advmedia.pre-change.json` | `cee1c0fa12375d177abc3f0126c228bfdac037e04d0c332ceea32ec31eb9e1d1` |
| `astv_ha_mplayer_engine.pre-change.json` | `8a861456739cf95bfa6c81670744d0c44e63a86d357958e1e70bfe9a6469beb6` |
| `README.md` | `e7627acda1f27bd8b7cf1e8d567ed935de2f9aae0a5f74a52dd11f324a533799` |

The documented restoration order is engine first, then adapter, followed by
fresh hash reads and both legacy regressions.

## Installed definitions

| Script | Installed hash | Category preserved |
| --- | --- | --- |
| `script.astv_adapter_advmedia` | `fe00d0cea795cc06` | Yes |
| `script.astv_ha_mplayer_engine` | `7f2e5588e9a9cedb` | Yes |

The adapter now accepts exactly one complete input shape:

- v1: `media_catalogue`, `media_item_id`, and `media_player`, with optional
  `media_profile`; this calls only `script.advmedia_prepare_playback`;
- v2: complete `media_record`, `selected_execution_method`, and `media_player`,
  with optional `media_profile`; this calls only the dormant
  `script.advmedia_process_media_record` entry point; or
- mixed, partial, and absent shapes stop with explicit errors.

Both successful shapes capture the complete child response as
`advmedia_response`, extract `advmedia_response.playback_payload`, and return
that payload as `payload_response`.

The HA Media Player engine now treats `execution_method` and `media_record` as a
pair. When both are present it passes the complete record, selected method, and
selected endpoint directly to the ASTV adapter. When neither is present it uses
the unchanged legacy provider path. A partial pair stops explicitly. Both
successful branches converge on exactly one final `media_player.play_media`
action.

Home Assistant accepted both stored definitions and re-read them with the hashes
above. Validation warned that the dormant core was not in the service registry,
as expected, and also reported template/dynamic-target advisories inherent in
the conditional input-presence and selected-endpoint design. No reload or
restart was performed.

## Live legacy regressions

Both tests used the normal UID entry path and completed successfully on the
kitchen speaker.

| Case | Result | Relevant trace IDs |
| --- | --- | --- |
| Classic FM / Radio Browser (`7AB06354E000`) | Legacy flags were both false; provider handler and Radio Browser ran; one final playback action loaded Classic FM. | UID `75fad16d33736b73c87d38998c4bd88b`; Select Intent `a7a9d3c5fa3f0d9b7e26bf8864c15e46`; Dispatcher `c6b4d36e4478dc14d9edc3985c413442`; HA engine `450e9a455ac27543b77c6e2889c20207`; Handle Provider `df65ef5caeac6d16986953a61752b375`; Radio Browser `50de783ca2df9057d5d805100a36ce0e` |
| BBC Radio 2 / legacy AdvMedia (`DEADBEEF`) | Legacy flags were both false; adapter selected only v1, called `advmedia_prepare_playback`, extracted the payload, and one final playback action loaded BBC Radio 2. | UID `c866bac5429200626f26fa55694f51cb`; Select Intent `d360e2fc4de2bf45252f25c8d56437ae`; Dispatcher `c64ac08670d9f25e7af4bd1600c13032`; HA engine `b25691d9b43fcde9b05b247863bff8be`; Handle Provider `9cf53f0496ff36395e55dcac8834e8d8`; Adapter `1d8a8741fc5e81a39b307d32c3cab771`; AdvMedia prepare `5c0cba55042e5a315de2f1922f873a7c` |

A focused direct v1 adapter call also returned the expected BBC Radio 2 payload
without playback (`72c8e2c9bbdd271f6bc79c205ede48f1`). Invalid adapter calls did not advance
the latest AdvMedia-prepare or provider-handler traces.

## Failure validation

| Component and case | Trace | Result |
| --- | --- | --- |
| Adapter: incomplete v1 | `3303b2a76080708f5bb3efbb3ec68e9c` | Explicit stop before child call |
| Adapter: incomplete v2 | `b7bcd6b05a5db50bb1c2c41bc15ab87d` | Explicit stop before child call |
| Adapter: mixed v1/v2 | `11d96534e7d684c64feb0e1424454ffc` | Explicit mixed-shape stop |
| Adapter: absent shape | `1a5133b64ee87f8c5fa37ee4444a981d` | Explicit stop before child call |
| Engine: record only | `f5bf88f22e74e2d78ecdf2e05cccfeb8` | Explicit incomplete-handoff stop; no child or playback |
| Engine: method only | `494bb01962f34cd8746c7300a47cd56a` | Explicit incomplete-handoff stop; no child or playback |

## Non-live v2 proof

Home Assistant template evaluation proved request composition without invoking
the undeployed core:

| Fixture | Request ID | Result |
| --- | --- | --- |
| Direct URL normalized record | `876975` | Selected normalized branch; preserved the complete record and unknown additive field; mapped method to `ha_mplayer`; preserved `media_player.kitchen_speaker`. |
| HA media-source normalized record | `877461` | Same result, preserving source type, provider, URI, media type, and additive field. |
| Adapter shape matrix | `876492` | Only complete v1 and complete v2 selected their paths; neither, partial, and mixed shapes selected rejection. |
| Response extraction | `875917` | Complete representative AdvMedia result remained intact locally; only `playback_payload` became the ASTV payload and final playback data. |

An installed-definition structural audit passed 13 assertions: exclusive adapter
branches; v1-only prepare call; v2-only core call; identical payload extraction;
no v2 catalogue/source lookup; normalized engine branch calls only the adapter;
legacy source access and provider call occur only in the legacy branch; exactly
one shared final playback action; and neither normalized layer has
`continue_on_error` or a legacy fallback. Therefore a v2 core failure aborts the
selected normalized branch before final playback. This is a structural
inference, not a live core invocation.

AdvMedia implementation evidence was read-only: recorded completion evidence for
ASTV-27, ASTV-58, and ASTV-59 reports translator, processing-core, generic, and
Google Cast implementation with passing suites, but those components remain
undeployed. Current live service discovery returned zero services matching
`advmedia_process_media_record`.

## Scope and limitations

- Unchanged live definitions included `script.astv_handle_provider`
  (`9e9a464e0240689c`), `script.astv_provider_radiobrowser`
  (`209c0bb88643a554`), and `script.astv_select_execution_engine`
  (`9d2eedaeba1f5b86`).
- No live normalized playback was attempted. Activation and coordinated
  cross-product live proof remain separately governed work.
- No provider, dispatcher, intent/endpoint record, AdvMedia or MediaCat runtime,
  production snapshot, central registry, or current-production diagram was
  changed.

