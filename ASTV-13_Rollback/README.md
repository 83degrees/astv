# ASTV-13 rollback

Date: 2026-08-11

The exact live pre-retirement Home Assistant configuration is preserved in full backup `172b43b6`, named `ASTV-13_pre_retirement_2026-08-11`.

Verified pre-retirement SHA-256 values:

- `/config/packages/astv/astv_scripts.yaml`: `871B6B8F7F3B292721E284C16407B3909420A7E085E7BECC7541000471220504`
- `/config/assistive/astv_tags2.yaml`: `C348EEF1FC1E19796CEB2695941C536436951C158EC3E24E0F5F951819ED3563`

The package and data snapshots in this directory preserve the legacy function and its data in human-readable form. The full Home Assistant backup is the byte-exact recovery source.

To restore only the retired components without restoring the full Home Assistant backup:

1. Restore `starburst/packages/astv/astv_scripts.yaml` to `/config/packages/astv/astv_scripts.yaml`.
2. Restore `starburst/assistive/astv_tags2.yaml` to `/config/assistive/astv_tags2.yaml`.
3. Run Home Assistant configuration validation.
4. Reload scripts only.
5. Confirm `script.astv_find_uid_record` is available before invoking it.

Restoring the full backup is a last-resort alternative because it restores broader Home Assistant configuration and restarts Home Assistant.
