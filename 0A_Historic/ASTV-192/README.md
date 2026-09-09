# ASTV-192 provider compatibility quarantine

This directory is a non-runtime, non-authoritative preservation area created before simplifying the active ASTV Media compatibility path.

Contents are retained as historical/reference implementation only. They are not a supported ASTV fallback or current interface, and nothing in this directory is loaded by Home Assistant.

The provider-era logic is being retained deliberately so that future provider-specific design work (for example Plex, Spotify, or similar services) can inspect the former implementation without requiring it to remain in the active runtime graph.

Source issue: ASTV-192
Source runtime file at pickup: `04_Source/config/packages/astv/astv_scripts.yaml`
Source blob SHA at pickup: `82e931381f86c31e6a63e519569ed8f17835eecc`

Retention rule: do not treat this quarantine as architecture or contract authority.