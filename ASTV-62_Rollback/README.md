# ASTV-62 coordinated rollback

This package contains the exact two live ASTV script definitions captured on
2026-08-24 immediately before the ASTV-62 installation. Treat both definitions
as one rollback unit.

| Script | Pre-change stable configuration hash | Category | Snapshot |
| --- | --- | --- | --- |
| `script.astv_adapter_advmedia` | `1ddc07631782c3a4` | `01KY5BCDDWE2CK0HM5RT0KXTNX` (`ASTV (Providers)`) | `astv_adapter_advmedia.pre-change.json` |
| `script.astv_ha_mplayer_engine` | `62a363022c26ca89` | `01K9QMV1C04YWV4HAS8G6V7FRV` (`Assistive Tech`) | `astv_ha_mplayer_engine.pre-change.json` |

## Coordinated restoration procedure

1. Retrieve both current live definitions and stable hashes. Confirm they match
   the reviewed ASTV-62 installed definitions. Stop and investigate unexpected
   drift.
2. Restore `astv_ha_mplayer_engine` first from its complete snapshot, using its
   retained category and freshly retrieved hash as the optimistic-lock value.
   This removes the normalized caller path before the adapter is restored.
3. Restore `astv_adapter_advmedia` from its complete snapshot with its retained
   category and a fresh optimistic-lock hash.
4. Allow each narrow script configuration update to make the saved definition
   queryable. Do not reload unrelated configuration and do not restart Home
   Assistant.
5. Re-read both definitions and confirm structural identity with the captured
   `config` objects. Confirm the resulting stable hashes are
   `62a363022c26ca89` and `1ddc07631782c3a4` respectively.
6. Re-read `script.astv_handle_provider` and
   `script.astv_provider_radiobrowser`; confirm their hashes remain
   `9e9a464e0240689c` and `209c0bb88643a554`.
7. Re-run the Classic FM and BBC Radio 2 normal-entry legacy regressions before
   returning the system to normal use.

If either restoration step fails, do not continue normal operation with a
partial engine/adapter boundary. Complete restoration of both definitions or
escalate the exact failure and current hashes.

This package changes no provider, dispatcher, intent or endpoint data, AdvMedia
implementation, MediaCat implementation, contract registry, or architecture
diagram.
