# ASTV-76 rollback

This package contains the exact pre-change live configuration returned for
`script.astv_adapter_advmedia` before ASTV-76 deployment.

- Live pre-change configuration hash: `fe00d0cea795cc06`
- Home Assistant category: `01KY5BCDDWE2CK0HM5RT0KXTNX` (`ASTV (Providers)`)
- Captured definition: `astv_adapter_advmedia.pre-change.json`

If rollback is required, first re-read the live script and verify the installed
hash is the ASTV-76 deployed hash recorded in `ASTV-76_VALIDATION.md`. Restore
the `config` object through the Home Assistant script configuration API using
optimistic locking, retain the category above, and re-read the script to verify
the restored hash is `fe00d0cea795cc06`. No restart is expected.

Do not restore this branch after ASTV-67 changes the separately owned
`script.advmedia_prepare_playback` entry contract without first reconciling that
later work instruction and its rollback package.
