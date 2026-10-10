"""Repository-exact tests for the ASTV Intent Catalogue provider."""

from __future__ import annotations

import asyncio
from enum import Enum
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import MappingProxyType, ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).parents[1]
INTEGRATION = ROOT / "custom_components" / "astv_intent_catalogue"
FIXTURES = ROOT / "05_Tests" / "fixtures" / "astv_intent_catalogue" / "v1"
PACKAGE = "custom_components.astv_intent_catalogue"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


package = ModuleType(PACKAGE)
package.__path__ = [str(INTEGRATION)]
sys.modules[PACKAGE] = package
const = _load_module(f"{PACKAGE}.const", INTEGRATION / "const.py")
catalogue = _load_module(f"{PACKAGE}.catalogue", INTEGRATION / "catalogue.py")


def _install_home_assistant_stubs() -> None:
    vol = ModuleType("voluptuous")

    class Invalid(ValueError):
        pass

    class Required:
        def __init__(self, key):
            self.key = key

        def __hash__(self):
            return hash(self.key)

    class Optional(Required):
        def __init__(self, key, default=None):
            super().__init__(key)
            self.default = default

    class Schema:
        def __init__(self, schema):
            self.schema = schema

    vol.Invalid = Invalid
    vol.Required = Required
    vol.Optional = Optional
    vol.Schema = Schema
    sys.modules["voluptuous"] = vol

    homeassistant = ModuleType("homeassistant")
    config_entries = ModuleType("homeassistant.config_entries")
    core = ModuleType("homeassistant.core")
    exceptions = ModuleType("homeassistant.exceptions")
    helpers = ModuleType("homeassistant.helpers")
    service_helper = ModuleType("homeassistant.helpers.service")
    typing_module = ModuleType("homeassistant.helpers.typing")

    class ConfigEntryState(Enum):
        LOADED = "loaded"
        SETUP_ERROR = "setup_error"

    class ConfigEntry:
        def __init__(self, entry_id="entry-1", state=ConfigEntryState.LOADED):
            self.entry_id = entry_id
            self.state = state

    class ConfigFlow:
        def __init_subclass__(cls, *, domain=None, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.domain = domain

        def __init__(self):
            self.current_entries = []

        def _async_current_entries(self):
            return self.current_entries

        def async_abort(self, *, reason):
            return {"type": "abort", "reason": reason}

        def async_create_entry(self, *, title, data):
            return {"type": "create_entry", "title": title, "data": data}

        def async_show_form(self, *, step_id):
            return {"type": "form", "step_id": step_id}

    class SupportsResponse(Enum):
        ONLY = "only"

    class ServiceCall:
        def __init__(self, data, user_id=None):
            self.data = data
            self.context = SimpleNamespace(user_id=user_id)

    class ConfigEntryError(RuntimeError):
        pass

    class ServiceValidationError(RuntimeError):
        pass

    class Unauthorized(RuntimeError):
        pass

    def async_register_admin_service(
        hass, domain, service, handler, schema=None, supports_response=None
    ):
        async def admin_handler(call):
            if call.context.user_id:
                user = await hass.auth.async_get_user(call.context.user_id)
                if user is None or not user.is_admin:
                    raise Unauthorized()
            return await handler(call)

        hass.services.async_register(
            domain,
            service,
            admin_handler,
            schema=schema,
            supports_response=supports_response,
            admin_only=True,
        )

    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigEntryState = ConfigEntryState
    config_entries.ConfigFlow = ConfigFlow
    config_entries.ConfigFlowResult = dict
    core.HomeAssistant = object
    core.ServiceCall = ServiceCall
    core.ServiceResponse = dict
    core.SupportsResponse = SupportsResponse
    exceptions.ConfigEntryError = ConfigEntryError
    exceptions.ServiceValidationError = ServiceValidationError
    exceptions.Unauthorized = Unauthorized
    service_helper.async_register_admin_service = async_register_admin_service
    typing_module.ConfigType = dict

    homeassistant.config_entries = config_entries
    homeassistant.core = core
    homeassistant.exceptions = exceptions
    homeassistant.helpers = helpers
    helpers.typing = typing_module
    helpers.service = service_helper
    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.exceptions"] = exceptions
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.service"] = service_helper
    sys.modules["homeassistant.helpers.typing"] = typing_module


_install_home_assistant_stubs()
administration = _load_module(
    f"{PACKAGE}.administration", INTEGRATION / "administration.py"
)
integration = _load_module(PACKAGE, INTEGRATION / "__init__.py")
config_flow = _load_module(f"{PACKAGE}.config_flow", INTEGRATION / "config_flow.py")


class FakeServices:
    def __init__(self):
        self.registration = None
        self.registrations = {}

    def async_register(self, domain, service, handler, **kwargs):
        registration = (domain, service, handler, kwargs)
        if self.registration is None:
            self.registration = registration
        self.registrations[(domain, service)] = registration

    def handler(self, domain, service):
        return self.registrations[(domain, service)][2]


class FakeConfigEntries:
    def __init__(self, entries=None):
        self.entries = list(entries or [])

    def async_entries(self, domain):
        return self.entries


class FakeHass:
    def __init__(self, entries=None):
        self.data = {}
        self.services = FakeServices()
        self.config_entries = FakeConfigEntries(entries)
        self.auth = SimpleNamespace(async_get_user=self._async_get_user)
        self.users = {}

    async def _async_get_user(self, user_id):
        return self.users.get(user_id)

    async def async_add_executor_job(self, target, *args):
        return target(*args)


def _load(path: Path):
    return catalogue.load_registry(path)


class CatalogueLoaderTests(unittest.TestCase):
    def test_all_documented_valid_fixtures_load(self) -> None:
        for path in sorted((FIXTURES / "valid").glob("*.yaml")):
            with self.subTest(path=path.name):
                registry = _load(path)
                self.assertEqual(registry.schema_id, "astv.intent_catalogue")
                self.assertEqual(registry.schema_version, "1.0.0")
                self.assertTrue(registry.active_revision.startswith("sha256:"))

    def test_all_documented_invalid_fixtures_are_rejected(self) -> None:
        for path in sorted((FIXTURES / "invalid").glob("*.yaml")):
            with self.subTest(path=path.name):
                with self.assertRaises(catalogue.CatalogueValidationError):
                    _load(path)

    def test_duplicate_raw_yaml_keys_are_rejected(self) -> None:
        raw = b"""schema: astv.intent_catalogue
schema: astv.intent_catalogue
schema_version: \"1.0.0\"
records: {}
"""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.yaml"
            path.write_bytes(raw)
            with self.assertRaisesRegex(
                catalogue.CatalogueValidationError, "duplicate key"
            ):
                _load(path)

    def test_aliases_and_multiple_documents_are_rejected(self) -> None:
        candidates = (
            b"schema: &schema astv.intent_catalogue\nschema_version: '1.0.0'\nrecords: {}\n",
            b"schema: astv.intent_catalogue\nschema_version: '1.0.0'\nrecords: {}\n---\n{}\n",
        )
        for raw in candidates:
            with self.subTest(raw=raw):
                with TemporaryDirectory() as directory:
                    path = Path(directory) / "invalid.yaml"
                    path.write_bytes(raw)
                    with self.assertRaises(catalogue.CatalogueValidationError):
                        _load(path)

    def test_merge_keys_and_unquoted_schema_version_are_rejected(self) -> None:
        candidates = (
            b"schema: astv.intent_catalogue\nschema_version: 1.0.0\nrecords: {}\n",
            b"schema: astv.intent_catalogue\nschema_version: '1.0.0'\nrecords:\n  item:\n    <<: {intent: routine.run}\n",
        )
        for raw in candidates:
            with self.subTest(raw=raw):
                with TemporaryDirectory() as directory:
                    path = Path(directory) / "invalid.yaml"
                    path.write_bytes(raw)
                    with self.assertRaises(catalogue.CatalogueValidationError):
                        _load(path)

    def test_production_candidate_is_exact_accepted_eight_record_fixture(self) -> None:
        candidate_path = (
            ROOT
            / "04_Implementation"
            / "haos"
            / "source"
            / "config"
            / "astv"
            / "astv_intent_catalogue.yaml"
        )
        fixture_path = FIXTURES / "valid" / "current_baseline_migrated.yaml"
        legacy_path = FIXTURES / "legacy" / "current_baseline_unversioned.yaml"

        candidate_document = yaml.safe_load(candidate_path.read_text(encoding="utf-8"))
        fixture_document = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
        legacy_records = yaml.safe_load(legacy_path.read_text(encoding="utf-8"))

        self.assertEqual(candidate_document, fixture_document)
        self.assertEqual(candidate_document["records"], legacy_records)
        self.assertEqual(len(candidate_document["records"]), 8)

    def test_revision_uses_normalized_content_not_yaml_serialization(self) -> None:
        first = b'''schema: astv.intent_catalogue
schema_version: "1.0.0"
records:
  evening:
    intent: routine.run
    title: Evening
    params: {}
    routine: evening
'''
        equivalent = b'''# Serialization-only changes must not affect identity.
records: {evening: {routine: evening, params: {}, title: Evening, intent: routine.run}}
schema_version: '1.0.0'
schema: astv.intent_catalogue
'''
        with TemporaryDirectory() as directory:
            first_path = Path(directory) / "first.yaml"
            equivalent_path = Path(directory) / "equivalent.yaml"
            first_path.write_bytes(first)
            equivalent_path.write_bytes(equivalent)

            first_registry = _load(first_path)
            equivalent_registry = _load(equivalent_path)

        self.assertEqual(
            first_registry.active_revision, equivalent_registry.active_revision
        )
        self.assertEqual(
            first_registry.lookup("evening"), equivalent_registry.lookup("evening")
        )

    def test_revision_changes_when_normalized_content_changes(self) -> None:
        original = b'''schema: astv.intent_catalogue
schema_version: "1.0.0"
records:
  evening:
    intent: routine.run
    title: Evening
    params: {}
    routine: evening
'''
        changed = original.replace(b"title: Evening", b"title: Evening routine")
        with TemporaryDirectory() as directory:
            original_path = Path(directory) / "original.yaml"
            changed_path = Path(directory) / "changed.yaml"
            original_path.write_bytes(original)
            changed_path.write_bytes(changed)

            original_registry = _load(original_path)
            changed_registry = _load(changed_path)

        self.assertNotEqual(
            original_registry.active_revision, changed_registry.active_revision
        )


class ImmutableRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = _load(
            FIXTURES / "valid" / "current_baseline_migrated.yaml"
        )

    def test_normalized_and_blank_lookup_contract(self) -> None:
        found = self.registry.lookup("  CLASSIC_FM ")
        self.assertTrue(found["ok"])
        self.assertTrue(found["found"])
        self.assertEqual(found["normalized_intent_id"], "classic_fm")
        self.assertNotIn("intent_id", found["record"])

        missing = self.registry.lookup("   ")
        self.assertFalse(missing["found"])
        self.assertEqual(missing["normalized_intent_id"], "")
        self.assertEqual(missing["record"], {})

    def test_active_tree_is_deeply_immutable_and_responses_are_detached(self) -> None:
        self.assertIsInstance(self.registry.records, MappingProxyType)
        with self.assertRaises(TypeError):
            self.registry.records["classic_fm"]["title"] = "changed"
        with self.assertRaises(TypeError):
            self.registry.records["classic_fm"]["params"]["output"][
                "domain"
            ] = "changed"

        first = self.registry.lookup("classic_fm")
        first["record"]["params"]["output"]["domain"] = "changed"
        self.assertEqual(
            self.registry.lookup("classic_fm")["record"]["params"]["output"][
                "domain"
            ],
            "audio",
        )

    def test_failed_replacement_preserves_active_object_and_revision(self) -> None:
        provider = catalogue.CatalogueProvider()
        provider.publish(self.registry)
        prior = provider.active
        with self.assertRaises(catalogue.CatalogueValidationError):
            _load(FIXTURES / "invalid" / "unknown_field.yaml")
        self.assertIs(provider.active, prior)
        self.assertEqual(provider.active.active_revision, self.registry.active_revision)


class IntegrationLifecycleTests(unittest.TestCase):
    def test_ui_flow_creates_only_one_empty_data_entry(self) -> None:
        flow = config_flow.AstvIntentCatalogueConfigFlow()
        form = asyncio.run(flow.async_step_user())
        self.assertEqual(form, {"type": "form", "step_id": "user"})
        created = asyncio.run(flow.async_step_user({}))
        self.assertEqual(created["type"], "create_entry")
        self.assertEqual(created["data"], {})

        flow.current_entries = [object()]
        aborted = asyncio.run(flow.async_step_user())
        self.assertEqual(aborted["reason"], "single_instance_allowed")

    def test_setup_registers_response_only_action_before_entry_load(self) -> None:
        hass = FakeHass()
        self.assertTrue(asyncio.run(integration.async_setup(hass, {})))
        domain, service, _, kwargs = hass.services.registration
        self.assertEqual((domain, service), (const.DOMAIN, const.SERVICE_LOOKUP))
        self.assertEqual(
            kwargs["supports_response"], integration.SupportsResponse.ONLY
        )

    def test_handler_distinguishes_unavailable_entry_from_unknown_id(self) -> None:
        entry = integration.ConfigEntry(state=integration.ConfigEntryState.SETUP_ERROR)
        hass = FakeHass([entry])
        asyncio.run(integration.async_setup(hass, {}))
        handler = hass.services.registration[2]
        with self.assertRaises(integration.ServiceValidationError):
            asyncio.run(handler(integration.ServiceCall({"intent_id": "unknown"})))

        entry.state = integration.ConfigEntryState.LOADED
        provider = catalogue.CatalogueProvider()
        provider.publish(
            _load(FIXTURES / "valid" / "current_baseline_migrated.yaml")
        )
        hass.data[const.DOMAIN][entry.entry_id] = provider
        response = asyncio.run(
            handler(integration.ServiceCall({"intent_id": "unknown"}))
        )
        self.assertFalse(response["found"])
        self.assertEqual(response["record"], {})

    def test_setup_entry_failure_leaves_no_active_registry(self) -> None:
        entry = integration.ConfigEntry()
        hass = FakeHass([entry])
        with patch.object(
            integration,
            "load_registry",
            side_effect=catalogue.CatalogueValidationError("invalid candidate"),
        ):
            with self.assertRaises(integration.ConfigEntryError):
                asyncio.run(integration.async_setup_entry(hass, entry))
        self.assertNotIn(entry.entry_id, hass.data.get(const.DOMAIN, {}))

    def test_setup_restart_and_unload_rebuild_then_release_registry(self) -> None:
        entry = integration.ConfigEntry()
        hass = FakeHass([entry])
        registry = _load(FIXTURES / "valid" / "current_baseline_migrated.yaml")
        with patch.object(integration, "load_registry", return_value=registry):
            self.assertTrue(asyncio.run(integration.async_setup_entry(hass, entry)))
        first_provider = hass.data[const.DOMAIN][entry.entry_id]
        self.assertEqual(first_provider.lookup("classic_fm")["record"]["title"], "Play Classic FM")
        self.assertTrue(asyncio.run(integration.async_unload_entry(hass, entry)))
        self.assertIsNone(first_provider.active)

        with patch.object(integration, "load_registry", return_value=registry):
            self.assertTrue(asyncio.run(integration.async_setup_entry(hass, entry)))
        self.assertIsNot(hass.data[const.DOMAIN][entry.entry_id], first_provider)

    def test_failed_in_process_refresh_retains_active_reference(self) -> None:
        provider = catalogue.CatalogueProvider()
        active = _load(FIXTURES / "valid" / "current_baseline_migrated.yaml")
        provider.publish(active)
        hass = FakeHass()
        with patch.object(
            integration,
            "load_registry",
            side_effect=catalogue.CatalogueValidationError("invalid replacement"),
        ):
            with self.assertRaises(catalogue.CatalogueValidationError):
                asyncio.run(integration.async_refresh(hass, provider))
        self.assertIs(provider.active, active)
        self.assertEqual(provider.active.active_revision, active.active_revision)


class AdministrationContractTests(unittest.TestCase):
    def _manager(self, directory):
        catalogue_path = Path(directory) / "catalogue.yaml"
        draft_path = Path(directory) / "draft.yaml"
        catalogue_path.write_bytes(
            (FIXTURES / "valid" / "current_baseline_migrated.yaml").read_bytes()
        )
        provider = catalogue.CatalogueProvider()
        provider.publish(catalogue.load_registry(catalogue_path))
        manager = administration.AdministrationManager(
            provider, catalogue_path, draft_path
        )
        provider.administration = manager
        return provider, manager, catalogue_path, draft_path

    @staticmethod
    def _routine(title="Evening"):
        return {
            "intent": "routine.run",
            "title": title,
            "params": {},
            "routine": "evening",
        }

    def test_discovery_advertises_only_callable_astv_334_operations(self) -> None:
        response = administration.AdministrationManager.capabilities()
        self.assertTrue(response["ok"])
        self.assertFalse(response["activation_applicable"])
        self.assertNotIn("activation.explicit", response["capabilities"])
        self.assertNotIn(
            "references.mediacat.activation_check", response["capabilities"]
        )
        self.assertNotIn("activate", response["operations"])
        self.assertEqual(
            set(response["operations"].values()),
            {
                const.SERVICE_GET_ADMINISTRATION_CAPABILITIES,
                const.SERVICE_GET_ADMINISTRATION_STATUS,
                const.SERVICE_LIST_INTENT_RECORDS,
                const.SERVICE_GET_INTENT_RECORD,
                const.SERVICE_VALIDATE_INTENT_RECORD,
                const.SERVICE_VALIDATE_INTENT_CATALOGUE,
                const.SERVICE_CREATE_INTENT_RECORD,
                const.SERVICE_UPDATE_INTENT_RECORD,
                const.SERVICE_DELETE_INTENT_RECORD,
                const.SERVICE_DISCARD_INTENT_CATALOGUE_DRAFT,
            },
        )
        json.dumps(response)
        descriptions = yaml.safe_load((INTEGRATION / "services.yaml").read_text())
        self.assertEqual(
            set(descriptions),
            {const.SERVICE_LOOKUP, *response["operations"].values()},
        )
        self.assertNotIn("activate_intent_catalogue", descriptions)

    def test_status_active_list_get_pagination_and_detachment(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, _, _ = self._manager(directory)
            status = manager.status()
            self.assertEqual(status["active_revision"], provider.active.active_revision)
            self.assertEqual(status["persisted_revision"], provider.active.active_revision)
            self.assertEqual(status["draft_state"], "absent")
            self.assertEqual(status["editable_revision"], provider.active.active_revision)

            first = manager.list_records(2)
            self.assertEqual(first["count"], 2)
            self.assertEqual(first["total_count"], 8)
            self.assertIsNotNone(first["next_cursor"])
            second = manager.list_records(2, first["next_cursor"])
            self.assertGreater(
                second["records"][0]["intent_id"],
                first["records"][-1]["intent_id"],
            )

            result = manager.get_record("  CLASSIC_FM ")
            self.assertTrue(result["ok"])
            result["record"]["title"] = "changed"
            self.assertEqual(
                manager.get_record("classic_fm")["record"]["title"],
                "Play Classic FM",
            )
            self.assertEqual(manager.get_record("missing")["error"]["code"], "not_found")
            self.assertEqual(manager.get_record("   ")["error"]["code"], "invalid_request")

            changed = catalogue.build_registry(
                {
                    "schema": const.SCHEMA_ID,
                    "schema_version": const.SCHEMA_VERSION,
                    "records": {"only": self._routine()},
                }
            )
            provider.publish(changed)
            stale = manager.list_records(2, first["next_cursor"])
            self.assertEqual(stale["error"]["code"], "stale_revision")

    def test_side_effect_free_record_and_complete_candidate_validation(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, _, draft_path = self._manager(directory)
            active = provider.active
            valid_record = manager.validate_record("evening", self._routine())
            self.assertTrue(valid_record["valid"])
            invalid_record = manager.validate_record(
                "EVENING", {"intent": "unsupported", "title": "x", "params": {}}
            )
            self.assertEqual(invalid_record["error"]["refinement"], "invalid_record")

            candidate = {
                "schema_id": const.SCHEMA_ID,
                "schema_version": const.SCHEMA_VERSION,
                "records": {"evening": self._routine()},
            }
            valid_candidate = manager.validate_candidate(candidate)
            self.assertTrue(valid_candidate["valid"])
            invalid_candidate = manager.validate_candidate(
                {**candidate, "schema_version": "2.0.0"}
            )
            self.assertEqual(
                invalid_candidate["error"]["refinement"], "invalid_candidate"
            )
            self.assertIs(provider.active, active)
            self.assertFalse(draft_path.exists())

    def test_guarded_durable_crud_restart_and_discard_preserve_active(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, catalogue_path, draft_path = self._manager(directory)
            active = provider.active
            create = manager.mutate(
                "create", active.active_revision, "evening", self._routine()
            )
            self.assertTrue(create["ok"])
            self.assertTrue(draft_path.is_file())
            self.assertIs(provider.active, active)
            self.assertFalse(provider.lookup("evening")["found"])

            stale = manager.mutate(
                "create", active.active_revision, "another", self._routine()
            )
            self.assertEqual(stale["error"]["code"], "stale_revision")

            restarted_provider = catalogue.CatalogueProvider()
            restarted_provider.publish(catalogue.load_registry(catalogue_path))
            restarted = administration.AdministrationManager(
                restarted_provider, catalogue_path, draft_path
            )
            status = restarted.status()
            self.assertEqual(status["draft_revision"], create["draft_revision"])
            self.assertTrue(status["activation_required"])

            update = restarted.mutate(
                "update",
                create["draft_revision"],
                "evening",
                self._routine("Updated evening"),
            )
            self.assertTrue(update["ok"])
            delete = restarted.mutate(
                "delete", update["draft_revision"], "evening"
            )
            self.assertTrue(delete["ok"])
            discard = restarted.discard(delete["draft_revision"])
            self.assertTrue(discard["ok"])
            self.assertFalse(draft_path.exists())
            self.assertEqual(restarted_provider.active.active_revision, active.active_revision)

    def test_invalid_yaml_draft_is_reported_and_guardedly_discarded(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, _, draft_path = self._manager(directory)
            draft_path.write_text("records: [not: valid", encoding="utf-8")
            status = manager.status()
            self.assertEqual(status["draft_state"], "invalid")
            self.assertTrue(status["draft_revision"].startswith("sha256-bytes:"))
            blocked = manager.mutate(
                "create", provider.active.active_revision, "evening", self._routine()
            )
            self.assertEqual(blocked["error"]["code"], "dependency_unavailable")
            stale = manager.discard("wrong")
            self.assertEqual(stale["error"]["code"], "stale_revision")
            removed = manager.discard(status["draft_revision"])
            self.assertTrue(removed["ok"])

    def test_atomic_write_failure_preserves_prior_draft_and_active(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, _, draft_path = self._manager(directory)
            first = manager.mutate(
                "create", provider.active.active_revision, "evening", self._routine()
            )
            prior_bytes = draft_path.read_bytes()
            active = provider.active
            with patch.object(
                administration, "_atomic_write", side_effect=OSError("injected")
            ):
                failed = manager.mutate(
                    "update",
                    first["draft_revision"],
                    "evening",
                    self._routine("changed"),
                )
            self.assertEqual(failed["error"]["refinement"], "persistence_unavailable")
            self.assertEqual(draft_path.read_bytes(), prior_bytes)
            self.assertIs(provider.active, active)

    def test_final_record_delete_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            catalogue_path = Path(directory) / "catalogue.yaml"
            draft_path = Path(directory) / "draft.yaml"
            registry = catalogue.build_registry(
                {
                    "schema": const.SCHEMA_ID,
                    "schema_version": const.SCHEMA_VERSION,
                    "records": {"only": self._routine()},
                }
            )
            provider = catalogue.CatalogueProvider()
            provider.publish(registry)
            manager = administration.AdministrationManager(
                provider, catalogue_path, draft_path
            )
            result = manager.mutate("delete", registry.active_revision, "only")
            self.assertEqual(result["error"]["refinement"], "invalid_candidate")
            self.assertFalse(draft_path.exists())

    def test_service_registration_provider_unavailable_and_admin_enforcement(self) -> None:
        hass = FakeHass()
        self.assertTrue(asyncio.run(integration.async_setup(hass, {})))
        capabilities = asyncio.run(
            hass.services.handler(
                const.DOMAIN, const.SERVICE_GET_ADMINISTRATION_CAPABILITIES
            )(integration.ServiceCall({}))
        )
        self.assertTrue(capabilities["ok"])
        unavailable = asyncio.run(
            hass.services.handler(
                const.DOMAIN, const.SERVICE_GET_ADMINISTRATION_STATUS
            )(integration.ServiceCall({}))
        )
        self.assertEqual(unavailable["error"]["refinement"], "provider_state_unavailable")

        registration = hass.services.registrations[
            (const.DOMAIN, const.SERVICE_VALIDATE_INTENT_RECORD)
        ]
        self.assertTrue(registration[3]["admin_only"])
        for service in (
            const.SERVICE_VALIDATE_INTENT_RECORD,
            const.SERVICE_VALIDATE_INTENT_CATALOGUE,
            const.SERVICE_CREATE_INTENT_RECORD,
            const.SERVICE_UPDATE_INTENT_RECORD,
            const.SERVICE_DELETE_INTENT_RECORD,
            const.SERVICE_DISCARD_INTENT_CATALOGUE_DRAFT,
        ):
            registered = hass.services.registrations[(const.DOMAIN, service)]
            self.assertTrue(registered[3]["admin_only"])
            self.assertEqual(
                registered[3]["supports_response"], integration.SupportsResponse.ONLY
            )
        self.assertNotIn(
            (const.DOMAIN, "activate_intent_catalogue"), hass.services.registrations
        )
        handler = registration[2]
        hass.users["ordinary"] = SimpleNamespace(is_admin=False)
        with self.assertRaises(sys.modules["homeassistant.exceptions"].Unauthorized):
            asyncio.run(
                handler(
                    integration.ServiceCall(
                        {"intent_id": "evening", "record": self._routine()},
                        user_id="ordinary",
                    )
                )
            )

        # A system context without user_id passes the HA admin helper and reaches
        # the provider, where unavailability remains a structured outcome.
        system = asyncio.run(
            handler(
                integration.ServiceCall(
                    {"intent_id": "evening", "record": self._routine()}
                )
            )
        )
        self.assertEqual(system["error"]["refinement"], "provider_state_unavailable")

    def test_concurrent_service_writers_reject_one_stale_revision(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, _, _ = self._manager(directory)
            entry = integration.ConfigEntry()
            hass = FakeHass([entry])

            async def scenario():
                await integration.async_setup(hass, {})
                hass.data[const.DOMAIN][entry.entry_id] = provider
                handler = hass.services.handler(
                    const.DOMAIN, const.SERVICE_CREATE_INTENT_RECORD
                )
                expected = provider.active.active_revision
                return await asyncio.gather(
                    handler(
                        integration.ServiceCall(
                            {
                                "expected_revision": expected,
                                "intent_id": "evening",
                                "record": self._routine(),
                            }
                        )
                    ),
                    handler(
                        integration.ServiceCall(
                            {
                                "expected_revision": expected,
                                "intent_id": "late_evening",
                                "record": self._routine("Late evening"),
                            }
                        )
                    ),
                )

            responses = asyncio.run(scenario())
            self.assertEqual(sum(response["ok"] for response in responses), 1)
            failure = next(response for response in responses if not response["ok"])
            self.assertEqual(failure["error"]["code"], "stale_revision")
            self.assertEqual(manager.status()["draft_count"], 9)
            self.assertEqual(len(provider.active.records), 8)


class PackagingAndAdapterTests(unittest.TestCase):
    def test_manifest_and_hacs_metadata(self) -> None:
        manifest = json.loads((INTEGRATION / "manifest.json").read_text())
        hacs = json.loads((ROOT / "hacs.json").read_text())
        self.assertEqual(manifest["domain"], const.DOMAIN)
        self.assertEqual(manifest["version"], "0.2.0")
        self.assertTrue(manifest["config_flow"])
        self.assertTrue(manifest["single_config_entry"])
        self.assertEqual(hacs, {"name": "ASTV Intent Catalogue"})
        self.assertTrue((INTEGRATION / "brand" / "icon.png").is_file())

    def test_script_adapter_only_changes_lookup_boundary(self) -> None:
        scripts_path = (
            ROOT
            / "04_Implementation"
            / "haos"
            / "source"
            / "config"
            / "packages"
            / "astv"
            / "astv_scripts.yaml"
        )
        scripts = scripts_path.read_text(encoding="utf-8")
        adapter, remainder = scripts.split("  astv_find_area_domain_endpoints:", 1)
        self.assertIn("action: astv_intent_catalogue.lookup", adapter)
        self.assertIn("response_variable: intent_catalogue_response", adapter)
        self.assertIn("if intent_catalogue_response.found else {}", adapter)
        self.assertNotIn("!include ../../astv/astv_intent_catalogue.yaml", adapter)
        self.assertIn("astv_intent_gateway:", remainder)
        self.assertIn("intent_context:", remainder)
        self.assertIn("target_context:", remainder)
        self.assertIn("execution_context:", remainder)

        class HomeAssistantYamlLoader(yaml.SafeLoader):
            pass

        HomeAssistantYamlLoader.add_constructor(
            "!include", lambda loader, node: loader.construct_scalar(node)
        )
        document = yaml.load(scripts, Loader=HomeAssistantYamlLoader)
        script_definitions = document["script"]
        adapter_sequence = script_definitions["astv_find_intent_record"]["sequence"]
        self.assertEqual(adapter_sequence[1]["action"], "astv_intent_catalogue.lookup")
        self.assertEqual(
            adapter_sequence[1]["response_variable"], "intent_catalogue_response"
        )
        self.assertEqual(
            adapter_sequence[-1]["response_variable"], "intent_record_response"
        )

        media_dispatch = script_definitions["astv_intent_engine_media"]["sequence"][-1]
        self.assertEqual(media_dispatch["action"], "script.astv_select_execution_engine")
        self.assertEqual(
            set(media_dispatch["data"]),
            {"intent_context", "target_context", "execution_context"},
        )
        routine_dispatch = script_definitions["astv_intent_engine_routine"]["sequence"][-1]
        self.assertEqual(
            set(routine_dispatch["data"]),
            {"intent_context", "target_context", "execution_context"},
        )


if __name__ == "__main__":
    unittest.main()
