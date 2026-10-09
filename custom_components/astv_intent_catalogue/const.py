"""Constants for the ASTV Intent Catalogue integration."""

from pathlib import Path

DOMAIN = "astv_intent_catalogue"
SERVICE_LOOKUP = "lookup"

CATALOGUE_PATH = Path("/config/astv/astv_intent_catalogue.yaml")

SCHEMA_ID = "astv.intent_catalogue"
SCHEMA_VERSION = "1.0.0"
INTERFACE_ID = "astv.intent_catalogue.lookup"
INTERFACE_VERSION = "1.0.0"
