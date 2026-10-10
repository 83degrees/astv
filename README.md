# ASTV

ASTV is the governed Home Assistant intent and orchestration product for this
repository. Its first HACS-native component is the ASTV Intent Catalogue
provider at `custom_components/astv_intent_catalogue/`.

The provider exposes the read-only response action
`astv_intent_catalogue.lookup` after a single UI config entry loads the strict
schema-v1 catalogue from `/config/astv/astv_intent_catalogue.yaml`. The
ASTV-334 candidate also exposes normalized administration discovery, status,
active reads, admin-only structural validation, and guarded durable draft
create/update/delete/discard operations. Explicit activation is intentionally
not advertised or registered until ASTV-335.

Installation, configuration, Beta entry, production cutover, and rollback are
governed separately. Repository source alone does not claim that the component
is installed or active on a Home Assistant instance. See
`08_Deployment/ASTV_INTENT_CATALOGUE_INTEGRATION_MIGRATION_PLAN.md` for the
compatible integration/configuration cutover boundary.
