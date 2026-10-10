"""Constants for the ASTV Intent Catalogue integration."""

from pathlib import Path

DOMAIN = "astv_intent_catalogue"
SERVICE_LOOKUP = "lookup"

SERVICE_GET_ADMINISTRATION_CAPABILITIES = "get_administration_capabilities"
SERVICE_GET_ADMINISTRATION_STATUS = "get_administration_status"
SERVICE_LIST_INTENT_RECORDS = "list_intent_records"
SERVICE_GET_INTENT_RECORD = "get_intent_record"
SERVICE_VALIDATE_INTENT_RECORD = "validate_intent_record"
SERVICE_VALIDATE_INTENT_CATALOGUE = "validate_intent_catalogue"
SERVICE_CREATE_INTENT_RECORD = "create_intent_record"
SERVICE_UPDATE_INTENT_RECORD = "update_intent_record"
SERVICE_DELETE_INTENT_RECORD = "delete_intent_record"
SERVICE_DISCARD_INTENT_CATALOGUE_DRAFT = "discard_intent_catalogue_draft"
SERVICE_ACTIVATE_INTENT_CATALOGUE = "activate_intent_catalogue"

MEDIACAT_DOMAIN = "mediacat"
MEDIACAT_RESOLVE_MEDIA_RECORD = "resolve_media_record"

CATALOGUE_PATH = Path("/config/astv/astv_intent_catalogue.yaml")
DRAFT_PATH = Path("/config/astv/astv_intent_catalogue.draft.yaml")

SCHEMA_ID = "astv.intent_catalogue"
SCHEMA_VERSION = "1.0.0"
INTERFACE_ID = "astv.intent_catalogue.lookup"
INTERFACE_VERSION = "1.0.0"
ADMIN_INTERFACE_ID = "astv.intent_catalogue.administration"
ADMIN_INTERFACE_VERSION = "1.0.0"
