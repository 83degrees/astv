# ASTV-194 legacy provider and resolver quarantine

**Non-runtime, non-authoritative, historical/reference only.**

The definitions in `legacy_provider_resolver_definitions.yaml` are retained
for historical and reference use. They are not loaded or deployed by Home
Assistant, are not a supported fallback, and are not a current ASTV interface.
They are retained for later provider-specific design such as Plex or Spotify.

- Source issue: ASTV-194.
- Rollback baseline / starting SHA: `da146940de049c62408398ce7f2ad2c7c04d67db`.
- Source runtime file: `04_Source/config/packages/astv/astv_scripts.yaml`.
- Source Git blob: `1ea9a5bcb4886c4b36d88e52f17c2524f0841147`.

The preservation file contains the complete baseline definitions of exactly
`astv_handle_provider`, `astv_provider_radiobrowser`, `astv_resolver`,
`astv_resolver_v2`, and `astv_sound_tag_feedback`, verbatim and with their
original indentation.

Related legacy fragments already preserved by earlier work remain at
`0A_Historic/ASTV-192/legacy_ha_mplayer_provider_branch.yaml` and
`0A_Historic/ASTV-193/legacy_google_home_definitions.yaml`; those fragments
are referenced rather than duplicated here. The complete baseline commit is the
authoritative rollback mechanism.

`astv_sound_tag_feedback` is quarantined because, in the inspected live
configuration, it is wired only to the legacy resolvers.

Live proof coverage was limited to all 37 script configurations and 25 of 28
automation configurations inspected read-only through `ha-starburst-mcp-v2`
WebSocket. Three bedroom-light automations were unavailable. This is not a
filesystem-wide claim that no external caller exists.

Do not include, load, deploy, or treat this directory as runtime configuration,
architecture authority, contract authority, or evidence of a supported
fallback/current interface.
