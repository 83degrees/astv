# ASTV-20 rollback baseline

Accepted pre-cutover production configurations captured before the ASTV-20
Google Automation executor-interface normalisation on 2026-08-12.

| Script | Stable Home Assistant configuration hash | Snapshot |
| --- | --- | --- |
| `script.astv_select_execution_engine` | `7ddd59fd391617dd` | `astv_select_execution_engine.pre-cutover.json` |
| `script.astv_g_automation_engine` | `3b7f13a2f76bc49f` | `astv_g_automation_engine.pre-cutover.json` |

These files preserve the exact accepted pre-cutover definitions. If rollback
is required, restore both configurations together before restoring the
matching execution-dispatch contract and architecture documentation.

## Review-revision baseline

Before applying the 2026-08-12 review revision, the current post-cutover
definitions were captured separately:

| Script | Stable Home Assistant configuration hash | Snapshot | Snapshot SHA-256 |
| --- | --- | --- | --- |
| `script.astv_select_execution_engine` | `1c0b3ea458cfd2cf` | `astv_select_execution_engine.pre-review-revision.json` | `92BD226606BDF68948F54CDA4FF90306DCE6630653BAC18025C78240F3ACFD70` |
| `script.astv_g_automation_engine` | `6aa39b6b39d12378` | `astv_g_automation_engine.pre-review-revision.json` | `74E5B93110C019CDB7285A008BC86F2B3E84120CA1AFA2ED1A68D248C112E739` |

Use these two snapshots together to return to the accepted post-cutover state
immediately before the review revision. The original pre-cutover snapshots
remain available when the complete executor-interface normalization must be
rolled back.
