# ASTV-63 coordinated rollback

This package contains the exact two live ASTV script definitions captured on
2026-08-24 immediately before the ASTV-63 installation. Treat both definitions
as one rollback unit.

| Script | Pre-change stable configuration hash | Category | Snapshot |
| --- | --- | --- | --- |
| `script.astv_provider_g_assist` | `09cdf48a46000450` | `01KY5BCDDWE2CK0HM5RT0KXTNX` (`ASTV (Providers)`) | `astv_provider_g_assist.pre-change.json` |
| `script.astv_g_home_device_engine` | `d9edfefe78b6f590` | `01K9QMV1C04YWV4HAS8G6V7FRV` (`Assistive Tech`) | `astv_g_home_device_engine.pre-change.json` |

## Coordinated restoration procedure

1. Retrieve both current live definitions and stable hashes. Confirm they match
   the reviewed ASTV-63 installed definitions: provider
   `052ce3c242fe4e93` and engine `a51304a3b2c88287`. Stop and investigate
   unexpected drift.
2. Restore `astv_provider_g_assist` first from its complete snapshot, using its
   retained category and freshly retrieved hash as the optimistic-lock value.
3. Restore `astv_g_home_device_engine` from its complete snapshot with its
   retained category and a fresh optimistic-lock hash.
4. Allow each narrow script update to make the saved definition queryable. Do
   not reload unrelated configuration and do not restart Home Assistant.
5. Re-read both definitions and confirm structural identity with the captured
   `config` objects. Confirm the resulting stable hashes are
   `09cdf48a46000450` and `d9edfefe78b6f590` respectively.
6. Re-read `script.astv_cmd_builder_media` and
   `script.astv_select_execution_engine`; confirm their hashes remain
   `ee4b5a81ebcc30fa` and `9d2eedaeba1f5b86`.
7. Repeat the Smooth Radio, LBC Radio, and News Briefing normal-entry legacy
   regressions before returning the system to normal use.

If either restoration step fails, do not continue normal operation with a
partial engine/provider boundary. Complete restoration of both definitions or
escalate the exact failure and current hashes.

This package changes no command builder, dispatcher, intent or endpoint data,
MediaCat or AdvMedia implementation, Google Assistant SDK integration, contract
registry, or architecture diagram.
