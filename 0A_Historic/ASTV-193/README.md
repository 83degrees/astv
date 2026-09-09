# ASTV-193 Google Home implementation quarantine

**Non-runtime, non-authoritative, historical/reference only.**

- Source issue: ASTV-193 — Simplify ASTV Google Home provider compatibility.
- Baseline / rollback SHA: `66dea3ec74f5814aabac396b78503075423ae853`.
- Source: `04_Source/config/packages/astv/astv_scripts.yaml`.
- Source Git blob: `13a649d761a0dc39d5d788bef864ce10f8e8553d`.

`legacy_google_home_definitions.yaml` preserves the complete
`astv_g_home_device_engine` and `astv_provider_g_assist` definitions
verbatim from the baseline (including original indentation). This retains the
exact legacy request-shape branch, provider-specific intent/request_object
branch, field declarations, branch guards, command-builder arguments, default
append_target behaviour, unsupported-intent notification/error, and the
surrounding normalized implementation for reference.

This directory is outside `04_Source/config/` and Home Assistant-loaded
configuration/package paths. Do not include, load, deploy, or treat these
definitions as active configuration. They are not evidence of a supported
fallback or current interface, and are not a standalone deployment bundle.
The baseline commit is the complete repository rollback reference.

The preservation commit precedes runtime simplification. Provider remains a
valid normalized source attribute; preserving historical provider logic does
not deprecate the provider concept.
