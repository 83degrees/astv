"""Repository-exact tests for the ASTV Intent Catalogue provider."""

from __future__ import annotations

import asyncio
import base64
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


def _v030_active_page(active, limit: int, cursor: str | None = None):
    """Snapshot accepted v0.3.0 active pagination independently of v1.1 code."""
    ordered_ids = sorted(active.records)
    start = 0
    if cursor is not None:
        padded = cursor + "=" * (-len(cursor) % 4)
        cursor_value = json.loads(base64.b64decode(padded, altchars=b"-_", validate=True))
        assert cursor_value["revision"] == active.active_revision
        start = ordered_ids.index(cursor_value["last_id"]) + 1
    selected = ordered_ids[start : start + limit]
    next_cursor = None
    if selected and start + len(selected) < len(ordered_ids):
        raw = json.dumps(
            {"revision": active.active_revision, "last_id": selected[-1]},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        next_cursor = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return {
        "ok": True,
        "interface_id": const.ADMIN_INTERFACE_ID,
        "interface_version": "1.0.0",
        "schema_id": const.SCHEMA_ID,
        "schema_version": const.SCHEMA_VERSION,
        "active_revision": active.active_revision,
        "count": len(selected),
        "total_count": len(ordered_ids),
        "records": [
            {
                "intent_id": intent_id,
                "record": catalogue.detached_record(active.records[intent_id]),
            }
            for intent_id in selected
        ],
        "next_cursor": next_cursor,
    }


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
    components = ModuleType("homeassistant.components")
    frontend = ModuleType("homeassistant.components.frontend")
    http = ModuleType("homeassistant.components.http")
    panel_custom = ModuleType("homeassistant.components.panel_custom")
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

    class HomeAssistantError(RuntimeError):
        pass

    class Unauthorized(RuntimeError):
        pass

    class StaticPathConfig:
        def __init__(self, url_path, path, cache_headers=True):
            self.url_path = url_path
            self.path = path
            self.cache_headers = cache_headers

    def async_panel_exists(hass, url_path):
        return url_path in hass.panels

    async def async_register_panel(hass, **kwargs):
        hass.panels[kwargs["frontend_url_path"]] = kwargs

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
    exceptions.HomeAssistantError = HomeAssistantError
    exceptions.ServiceValidationError = ServiceValidationError
    exceptions.Unauthorized = Unauthorized
    service_helper.async_register_admin_service = async_register_admin_service
    typing_module.ConfigType = dict
    frontend.async_panel_exists = async_panel_exists
    http.StaticPathConfig = StaticPathConfig
    panel_custom.async_register_panel = async_register_panel

    homeassistant.config_entries = config_entries
    homeassistant.components = components
    components.frontend = frontend
    components.http = http
    components.panel_custom = panel_custom
    homeassistant.core = core
    homeassistant.exceptions = exceptions
    homeassistant.helpers = helpers
    helpers.typing = typing_module
    helpers.service = service_helper
    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.frontend"] = frontend
    sys.modules["homeassistant.components.http"] = http
    sys.modules["homeassistant.components.panel_custom"] = panel_custom
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
        self.calls = []

    def async_register(self, domain, service, handler, **kwargs):
        registration = (domain, service, handler, kwargs)
        if self.registration is None:
            self.registration = registration
        self.registrations[(domain, service)] = registration

    def handler(self, domain, service):
        return self.registrations[(domain, service)][2]

    def has_service(self, domain, service):
        return (domain, service) in self.registrations

    async def async_call(
        self, domain, service, service_data, *, blocking=False, return_response=False
    ):
        self.calls.append((domain, service, dict(service_data)))
        handler = self.handler(domain, service)
        call_type = sys.modules["homeassistant.core"].ServiceCall
        return await handler(call_type(service_data))


class FakeConfigEntries:
    def __init__(self, entries=None):
        self.entries = list(entries or [])
        self.reload_calls = []

    def async_entries(self, domain):
        return self.entries

    async def async_reload(self, entry_id):
        self.reload_calls.append(entry_id)
        return True


class FakeHass:
    def __init__(self, entries=None):
        self.data = {}
        self.services = FakeServices()
        self.config_entries = FakeConfigEntries(entries)
        self.auth = SimpleNamespace(async_get_user=self._async_get_user)
        self.users = {}
        self.panels = {}
        self.http = SimpleNamespace(
            paths=[], async_register_static_paths=self._async_register_static_paths
        )

    async def _async_get_user(self, user_id):
        return self.users.get(user_id)

    async def async_add_executor_job(self, target, *args):
        return target(*args)

    async def _async_register_static_paths(self, paths):
        self.http.paths.extend(paths)


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

    @staticmethod
    def _media(item_id="classic_fm", title="Media"):
        return {
            "intent": "media.play_source",
            "title": title,
            "params": {
                "output": {"domain": "audio"},
                "catalogue_id": "curated_media",
                "item_id": item_id,
            },
        }

    def test_discovery_advertises_callable_activation(self) -> None:
        response = administration.AdministrationManager.capabilities()
        self.assertTrue(response["ok"])
        self.assertTrue(response["activation_applicable"])
        self.assertIn("activation.explicit", response["capabilities"])
        self.assertIn("draft.list", response["capabilities"])
        self.assertIn("draft.get", response["capabilities"])
        self.assertIn(
            "references.mediacat.activation_check", response["capabilities"]
        )
        self.assertEqual(
            response["operations"]["activate"],
            const.SERVICE_ACTIVATE_INTENT_CATALOGUE,
        )
        self.assertEqual(
            response["operations"]["draft_list"],
            const.SERVICE_LIST_INTENT_RECORDS,
        )
        self.assertEqual(
            response["operations"]["draft_get"],
            const.SERVICE_GET_INTENT_RECORD,
        )
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
                const.SERVICE_ACTIVATE_INTENT_CATALOGUE,
            },
        )
        json.dumps(response)
        descriptions = yaml.safe_load((INTEGRATION / "services.yaml").read_text())
        self.assertEqual(
            set(descriptions),
            {const.SERVICE_LOOKUP, *response["operations"].values()},
        )
        self.assertIn("activate_intent_catalogue", descriptions)

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

    def test_v11_active_compatibility_and_service_view_schema(self) -> None:
        with TemporaryDirectory() as directory:
            _, manager, _, _ = self._manager(directory)
            omitted_list = manager.list_records(2)
            explicit_list = manager.list_records(2, view="active")
            omitted_get = manager.get_record("classic_fm")
            explicit_get = manager.get_record("classic_fm", view="active")

            self.assertEqual(omitted_list, explicit_list)
            self.assertEqual(omitted_get, explicit_get)
            self.assertEqual(omitted_list["interface_version"], "1.1.0")
            self.assertEqual(omitted_get["interface_version"], "1.1.0")
            self.assertNotIn("view", omitted_list)
            self.assertNotIn("source_revision", omitted_list)
            self.assertNotIn("view", omitted_get)
            cursor_value = json.loads(
                base64.urlsafe_b64decode(
                    omitted_list["next_cursor"]
                    + "=" * (-len(omitted_list["next_cursor"]) % 4)
                )
            )
            self.assertEqual(set(cursor_value), {"revision", "last_id"})

        self.assertEqual(integration._view_value("active"), "active")
        self.assertEqual(integration._view_value("draft"), "draft")
        for invalid in ("other", "", None, {}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(integration.vol.Invalid):
                    integration._view_value(invalid)

        list_schema = integration.LIST_SCHEMA.schema
        get_schema = integration.GET_SCHEMA.schema
        list_view = next(key for key in list_schema if key.key == "view")
        get_view = next(key for key in get_schema if key.key == "view")
        self.assertEqual(list_view.default, "active")
        self.assertEqual(get_view.default, "active")

    def test_v030_active_pagination_cursor_bytes_regression(self) -> None:
        expected_revision = (
            "sha256:98790a0ecc161e218e845c57a673ff6a4d54e984076b7eddc0547cd164638e8e"
        )
        expected_limit_two_cursors = [
            "eyJsYXN0X2lkIjoiY2xhc3NpY19mbSIsInJldmlzaW9uIjoic2hhMjU2Ojk4NzkwYTBlY2MxNjFlMjE4ZTg0NWM1N2E2NzNmZjZhNGQ1NGU5ODQwNzZiN2VkZGMwNTQ3Y2QxNjQ2MzhlOGUifQ",
            "eyJsYXN0X2lkIjoibGJjX25ld3MiLCJyZXZpc2lvbiI6InNoYTI1Njo5ODc5MGEwZWNjMTYxZTIxOGU4NDVjNTdhNjczZmY2YTRkNTRlOTg0MDc2YjdlZGRjMDU0N2NkMTY0NjM4ZThlIn0",
            "eyJsYXN0X2lkIjoibW9ybmluZ19yb3V0aW5lIiwicmV2aXNpb24iOiJzaGEyNTY6OTg3OTBhMGVjYzE2MWUyMThlODQ1YzU3YTY3M2ZmNmE0ZDU0ZTk4NDA3NmI3ZWRkYzA1NDdjZDE2NDYzOGU4ZSJ9",
            None,
        ]
        with TemporaryDirectory() as directory:
            provider, manager, _, _ = self._manager(directory)
            self.assertEqual(provider.active.active_revision, expected_revision)

            for limit in (1, 2, 3, 7, 8, 20):
                with self.subTest(limit=limit):
                    cursor = None
                    cursor_bytes = []
                    while True:
                        legacy = _v030_active_page(provider.active, limit, cursor)
                        expected_v11 = {**legacy, "interface_version": "1.1.0"}
                        omitted = manager.list_records(limit, cursor)
                        explicit = manager.list_records(limit, cursor, view="active")

                        self.assertEqual(omitted, expected_v11)
                        self.assertEqual(explicit, expected_v11)
                        self.assertEqual(omitted["next_cursor"], legacy["next_cursor"])
                        self.assertEqual(explicit["next_cursor"], legacy["next_cursor"])
                        cursor_bytes.append(legacy["next_cursor"])

                        cursor = legacy["next_cursor"]
                        if cursor is None:
                            break

                    if limit == 2:
                        self.assertEqual(cursor_bytes, expected_limit_two_cursors)

    def test_draft_projection_pagination_state_and_restart(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, catalogue_path, draft_path = self._manager(directory)
            absent_list = manager.list_records(view="draft")
            absent_get = manager.get_record("classic_fm", view="draft")
            self.assertEqual(absent_list["error"]["refinement"], "draft_not_found")
            self.assertEqual(absent_get["error"]["refinement"], "draft_not_found")
            self.assertEqual(absent_list["view"], "draft")
            self.assertIsNone(absent_list["draft_revision"])

            created = manager.mutate(
                "create", provider.active.active_revision, "evening", self._routine()
            )
            self.assertFalse(manager.get_record("evening")["ok"])
            draft_get = manager.get_record("  EVENING ", view="draft")
            self.assertTrue(draft_get["ok"])
            self.assertEqual(draft_get["source_revision"], created["draft_revision"])
            self.assertEqual(draft_get["active_revision"], provider.active.active_revision)
            draft_get["record"]["title"] = "detached"
            self.assertEqual(
                manager.get_record("evening", view="draft")["record"]["title"],
                "Evening",
            )

            entry = integration.ConfigEntry()
            hass = FakeHass([entry])

            async def read_through_services():
                await integration.async_setup(hass, {})
                hass.data[const.DOMAIN][entry.entry_id] = provider
                listed = await hass.services.handler(
                    const.DOMAIN, const.SERVICE_LIST_INTENT_RECORDS
                )(integration.ServiceCall({"view": "draft", "limit": 20}))
                found = await hass.services.handler(
                    const.DOMAIN, const.SERVICE_GET_INTENT_RECORD
                )(integration.ServiceCall({"view": "draft", "intent_id": "evening"}))
                return listed, found

            service_list, service_get = asyncio.run(read_through_services())
            self.assertEqual(service_list["view"], "draft")
            self.assertEqual(service_get["record"]["title"], "Evening")

            updated = manager.mutate(
                "update",
                created["draft_revision"],
                "evening",
                self._routine("Updated evening"),
            )
            restarted_provider = catalogue.CatalogueProvider()
            restarted_provider.publish(catalogue.load_registry(catalogue_path))
            restarted = administration.AdministrationManager(
                restarted_provider, catalogue_path, draft_path
            )
            self.assertEqual(
                restarted.get_record("evening", view="draft")["record"]["title"],
                "Updated evening",
            )

            first_page = restarted.list_records(2, view="draft")
            self.assertEqual(first_page["view"], "draft")
            self.assertEqual(first_page["source_revision"], updated["draft_revision"])
            self.assertIsNotNone(first_page["next_cursor"])
            second_page = restarted.list_records(
                2, first_page["next_cursor"], view="draft"
            )
            self.assertGreater(
                second_page["records"][0]["intent_id"],
                first_page["records"][-1]["intent_id"],
            )
            wrong_draft_cursor = restarted.list_records(
                2, restarted.list_records(2)["next_cursor"], view="draft"
            )
            self.assertEqual(
                wrong_draft_cursor["error"]["refinement"], "invalid_cursor"
            )
            wrong_active_cursor = restarted.list_records(
                2, first_page["next_cursor"], view="active"
            )
            self.assertEqual(
                wrong_active_cursor["error"]["refinement"], "invalid_cursor"
            )
            malformed = restarted.list_records(2, "not-base64", view="draft")
            self.assertEqual(malformed["error"]["refinement"], "invalid_cursor")
            json.dumps(first_page)

            changed = restarted.mutate(
                "update",
                updated["draft_revision"],
                "classic_fm",
                self._media(title="Changed classic"),
            )
            stale = restarted.list_records(2, first_page["next_cursor"], view="draft")
            self.assertEqual(stale["error"]["refinement"], "stale_cursor")
            self.assertEqual(stale["draft_revision"], changed["draft_revision"])
            self.assertEqual(
                restarted.get_record("classic_fm")["record"]["title"],
                "Play Classic FM",
            )
            self.assertEqual(
                restarted.get_record("classic_fm", view="draft")["record"]["title"],
                "Changed classic",
            )

            deleted = restarted.mutate(
                "delete", changed["draft_revision"], "classic_fm"
            )
            self.assertTrue(restarted.get_record("classic_fm")["ok"])
            deleted_get = restarted.get_record("classic_fm", view="draft")
            self.assertEqual(deleted_get["error"]["refinement"], "intent_not_found")
            self.assertEqual(deleted_get["normalized_intent_id"], "classic_fm")

    def test_draft_invalid_and_unavailable_read_outcomes(self) -> None:
        with TemporaryDirectory() as directory:
            _, manager, _, draft_path = self._manager(directory)
            draft_path.write_text("records: [torn", encoding="utf-8")
            invalid = manager.list_records(view="draft")
            self.assertEqual(
                invalid["error"]["refinement"], "draft_state_invalid"
            )
            self.assertTrue(invalid["draft_revision"].startswith("sha256-bytes:"))

            unavailable_observation = administration.StoredObservation("unavailable")
            with patch.object(
                administration, "_observe", return_value=unavailable_observation
            ):
                unavailable = manager.get_record("classic_fm", view="draft")
            self.assertEqual(
                unavailable["error"]["refinement"], "draft_state_unavailable"
            )
            self.assertIsNone(unavailable["draft_revision"])

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
            self.assertEqual(
                restarted.list_records(view="draft")["error"]["refinement"],
                "draft_not_found",
            )
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
            const.SERVICE_ACTIVATE_INTENT_CATALOGUE,
        ):
            registered = hass.services.registrations[(const.DOMAIN, service)]
            self.assertTrue(registered[3]["admin_only"])
            self.assertEqual(
                registered[3]["supports_response"], integration.SupportsResponse.ONLY
            )
        self.assertIn(
            (const.DOMAIN, "activate_intent_catalogue"), hass.services.registrations
        )
        for service in (
            const.SERVICE_LIST_INTENT_RECORDS,
            const.SERVICE_GET_INTENT_RECORD,
        ):
            registered = hass.services.registrations[(const.DOMAIN, service)]
            self.assertNotIn("admin_only", registered[3])
            self.assertEqual(
                registered[3]["supports_response"], integration.SupportsResponse.ONLY
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

    def test_activation_success_deduplicates_references_and_recovers_on_restart(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, catalogue_path, draft_path = self._manager(directory)
            active = provider.active
            create = manager.mutate(
                "create",
                active.active_revision,
                "classic_fm_alias",
                self._media("classic_fm", "Classic alias"),
            )
            entry = integration.ConfigEntry()
            hass = FakeHass([entry])

            async def resolve(call):
                return {"returned_record_version": 1, **call.data}

            async def scenario():
                await integration.async_setup(hass, {})
                hass.data[const.DOMAIN][entry.entry_id] = provider
                hass.services.async_register(
                    const.MEDIACAT_DOMAIN,
                    const.MEDIACAT_RESOLVE_MEDIA_RECORD,
                    resolve,
                )
                return await hass.services.handler(
                    const.DOMAIN, const.SERVICE_ACTIVATE_INTENT_CATALOGUE
                )(
                    integration.ServiceCall(
                        {"expected_revision": create["draft_revision"]}
                    )
                )

            visibility = []
            original_publish = provider.publish

            def observed_publish(replacement):
                visibility.append(provider.lookup("classic_fm_alias")["found"])
                original_publish(replacement)
                visibility.append(provider.lookup("classic_fm_alias")["found"])

            with patch.object(provider, "publish", side_effect=observed_publish):
                response = asyncio.run(scenario())

            self.assertTrue(response["ok"])
            self.assertEqual(visibility, [False, True])
            probes = [call[2] for call in hass.services.calls]
            self.assertEqual(len(probes), 7)
            self.assertEqual(len({tuple(sorted(probe.items())) for probe in probes}), 7)
            self.assertFalse(draft_path.exists())
            self.assertEqual(
                manager.get_record("classic_fm_alias", view="draft")["error"][
                    "refinement"
                ],
                "draft_not_found",
            )
            self.assertEqual(catalogue.load_registry(catalogue_path).active_revision,
                             response["active_revision"])
            status = manager.status()
            self.assertEqual(status["active_revision"], status["persisted_revision"])
            self.assertIsNone(status["last_activation_error"])
            self.assertEqual(hass.config_entries.reload_calls, [])

            restarted = catalogue.CatalogueProvider()
            restarted.publish(catalogue.load_registry(catalogue_path))
            restarted_manager = administration.AdministrationManager(
                restarted, catalogue_path, draft_path
            )
            self.assertTrue(restarted.lookup("classic_fm_alias")["found"])
            next_edit = restarted_manager.mutate(
                "create", restarted.active.active_revision, "evening", self._routine()
            )
            self.assertTrue(next_edit["ok"])

    def test_activation_distinguishes_absent_not_found_and_operational_failure(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, catalogue_path, draft_path = self._manager(directory)
            create = manager.mutate(
                "create",
                provider.active.active_revision,
                "missing_media",
                self._media("missing_item"),
            )
            prior_active = provider.active
            prior_persisted = catalogue_path.read_bytes()
            prior_draft = draft_path.read_bytes()
            entry = integration.ConfigEntry()

            async def activate_with(handler=None):
                hass = FakeHass([entry])
                await integration.async_setup(hass, {})
                hass.data[const.DOMAIN][entry.entry_id] = provider
                if handler is not None:
                    hass.services.async_register(
                        const.MEDIACAT_DOMAIN,
                        const.MEDIACAT_RESOLVE_MEDIA_RECORD,
                        handler,
                    )
                response = await hass.services.handler(
                    const.DOMAIN, const.SERVICE_ACTIVATE_INTENT_CATALOGUE
                )(
                    integration.ServiceCall(
                        {"expected_revision": create["draft_revision"]}
                    )
                )
                return response

            absent = asyncio.run(activate_with())
            self.assertEqual(absent["error"]["refinement"], "mediacat_unavailable")

            async def not_found(call):
                if call.data["item_id"] == "missing_item":
                    raise sys.modules[
                        "homeassistant.exceptions"
                    ].ServiceValidationError("not found")
                return {"returned_record_version": 1}

            missing = asyncio.run(activate_with(not_found))
            self.assertEqual(missing["error"]["code"], "activation_failed")
            self.assertEqual(
                missing["error"]["refinement"], "referenced_target_not_found"
            )
            self.assertEqual(len(missing["errors"]), 1)

            async def unavailable(call):
                raise sys.modules["homeassistant.exceptions"].HomeAssistantError(
                    "registry unavailable"
                )

            unavailable_response = asyncio.run(activate_with(unavailable))
            self.assertEqual(
                unavailable_response["error"]["code"], "dependency_unavailable"
            )
            self.assertIs(provider.active, prior_active)
            self.assertEqual(catalogue_path.read_bytes(), prior_persisted)
            self.assertEqual(draft_path.read_bytes(), prior_draft)
            status = manager.status()
            self.assertEqual(
                status["last_activation_error"]["refinement"], "mediacat_unavailable"
            )

    def test_invalid_draft_and_persisted_replace_failure_retain_prior_state(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, catalogue_path, draft_path = self._manager(directory)
            prior_active = provider.active
            prior_persisted = catalogue_path.read_bytes()
            draft_path.write_text("records: [torn", encoding="utf-8")
            invalid_revision = manager.status()["draft_revision"]
            preparation, invalid = manager.prepare_activation(invalid_revision)
            self.assertIsNone(preparation)
            self.assertEqual(invalid["error"]["refinement"], "candidate_invalid")
            self.assertIs(provider.active, prior_active)
            self.assertEqual(catalogue_path.read_bytes(), prior_persisted)

            manager.discard(invalid_revision)
            create = manager.mutate(
                "create", prior_active.active_revision, "evening", self._routine()
            )
            preparation, failure = manager.prepare_activation(create["draft_revision"])
            self.assertIsNone(failure)
            with patch.object(administration.os, "replace", side_effect=OSError("fail")):
                replace_failure = manager.commit_activation(
                    create["draft_revision"], preparation
                )
            self.assertEqual(
                replace_failure["error"]["refinement"], "persisted_replace_failed"
            )
            self.assertIs(provider.active, prior_active)
            self.assertEqual(catalogue_path.read_bytes(), prior_persisted)
            self.assertTrue(draft_path.exists())

    def test_post_commit_restart_reconciles_unknown_outcome(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, catalogue_path, draft_path = self._manager(directory)
            create = manager.mutate(
                "create", provider.active.active_revision, "evening", self._routine()
            )
            preparation, failure = manager.prepare_activation(create["draft_revision"])
            self.assertIsNone(failure)
            self.assertIsNone(
                manager.commit_activation(create["draft_revision"], preparation)
            )

            # Simulate process loss after the commit point and before the
            # in-memory publish/response. Cold start reconciles from persisted state.
            self.assertFalse(draft_path.exists())
            self.assertFalse(provider.lookup("evening")["found"])
            restarted = catalogue.CatalogueProvider()
            restarted.publish(catalogue.load_registry(catalogue_path))
            self.assertTrue(restarted.lookup("evening")["found"])
            self.assertEqual(
                restarted.active.active_revision, preparation.registry.active_revision
            )

    def test_concurrent_writer_and_activation_are_serialized(self) -> None:
        with TemporaryDirectory() as directory:
            provider, manager, _, _ = self._manager(directory)
            first = manager.mutate(
                "create", provider.active.active_revision, "evening", self._routine()
            )
            entry = integration.ConfigEntry()
            hass = FakeHass([entry])

            async def resolve(call):
                return {"returned_record_version": 1}

            async def scenario():
                await integration.async_setup(hass, {})
                hass.data[const.DOMAIN][entry.entry_id] = provider
                hass.services.async_register(
                    const.MEDIACAT_DOMAIN,
                    const.MEDIACAT_RESOLVE_MEDIA_RECORD,
                    resolve,
                )
                writer = hass.services.handler(
                    const.DOMAIN, const.SERVICE_CREATE_INTENT_RECORD
                )
                activate = hass.services.handler(
                    const.DOMAIN, const.SERVICE_ACTIVATE_INTENT_CATALOGUE
                )
                return await asyncio.gather(
                    writer(
                        integration.ServiceCall(
                            {
                                "expected_revision": first["draft_revision"],
                                "intent_id": "late_evening",
                                "record": self._routine("Late evening"),
                            }
                        )
                    ),
                    activate(
                        integration.ServiceCall(
                            {"expected_revision": first["draft_revision"]}
                        )
                    ),
                )

            writer_response, activation_response = asyncio.run(scenario())
            self.assertTrue(writer_response["ok"])
            self.assertEqual(
                activation_response["error"]["code"], "stale_revision"
            )
            self.assertFalse(provider.lookup("evening")["found"])
            self.assertEqual(
                manager.status()["draft_revision"], writer_response["draft_revision"]
            )


class InteroperabilityRegressionTests(unittest.TestCase):
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

    def test_manager_independent_service_lifecycle_and_exact_versions(self) -> None:
        """Exercise the complete public lifecycle without a product manager."""
        with TemporaryDirectory() as directory:
            provider, manager, _, draft_path = self._manager(directory)
            entry = integration.ConfigEntry()
            hass = FakeHass([entry])

            async def resolve_media(call):
                return {"returned_record_version": 1, **call.data}

            async def call(service, data=None):
                return await hass.services.handler(const.DOMAIN, service)(
                    integration.ServiceCall(data or {})
                )

            async def scenario():
                await integration.async_setup(hass, {})
                hass.data[const.DOMAIN][entry.entry_id] = provider
                hass.services.async_register(
                    const.MEDIACAT_DOMAIN,
                    const.MEDIACAT_RESOLVE_MEDIA_RECORD,
                    resolve_media,
                )

                capabilities = await call(
                    const.SERVICE_GET_ADMINISTRATION_CAPABILITIES
                )
                status = await call(const.SERVICE_GET_ADMINISTRATION_STATUS)
                listed = await call(
                    const.SERVICE_LIST_INTENT_RECORDS, {"limit": 200}
                )
                found = await call(
                    const.SERVICE_GET_INTENT_RECORD,
                    {"intent_id": "  CLASSIC_FM "},
                )
                validated_record = await call(
                    const.SERVICE_VALIDATE_INTENT_RECORD,
                    {"intent_id": "interop_probe", "record": self._routine()},
                )
                validated_candidate = await call(
                    const.SERVICE_VALIDATE_INTENT_CATALOGUE,
                    {
                        "candidate": {
                            "schema_id": const.SCHEMA_ID,
                            "schema_version": const.SCHEMA_VERSION,
                            "records": {"interop_probe": self._routine()},
                        }
                    },
                )

                created = await call(
                    const.SERVICE_CREATE_INTENT_RECORD,
                    {
                        "expected_revision": status["editable_revision"],
                        "intent_id": "interop_probe",
                        "record": self._routine(),
                    },
                )
                updated = await call(
                    const.SERVICE_UPDATE_INTENT_RECORD,
                    {
                        "expected_revision": created["draft_revision"],
                        "intent_id": "interop_probe",
                        "record": self._routine("Updated probe"),
                    },
                )
                deleted = await call(
                    const.SERVICE_DELETE_INTENT_RECORD,
                    {
                        "expected_revision": updated["draft_revision"],
                        "intent_id": "interop_probe",
                    },
                )
                discarded = await call(
                    const.SERVICE_DISCARD_INTENT_CATALOGUE_DRAFT,
                    {"expected_revision": deleted["draft_revision"]},
                )

                activation_create = await call(
                    const.SERVICE_CREATE_INTENT_RECORD,
                    {
                        "expected_revision": discarded["editable_revision"],
                        "intent_id": "interop_probe",
                        "record": self._routine(),
                    },
                )
                activated = await call(
                    const.SERVICE_ACTIVATE_INTENT_CATALOGUE,
                    {"expected_revision": activation_create["draft_revision"]},
                )
                activated_record = await call(
                    const.SERVICE_GET_INTENT_RECORD,
                    {"intent_id": "interop_probe"},
                )
                final_status = await call(
                    const.SERVICE_GET_ADMINISTRATION_STATUS
                )
                return {
                    "capabilities": capabilities,
                    "status": status,
                    "listed": listed,
                    "found": found,
                    "validated_record": validated_record,
                    "validated_candidate": validated_candidate,
                    "created": created,
                    "updated": updated,
                    "deleted": deleted,
                    "discarded": discarded,
                    "activated": activated,
                    "activated_record": activated_record,
                    "final_status": final_status,
                }

            results = asyncio.run(scenario())

            for response in results.values():
                self.assertTrue(response["ok"])
                self.assertEqual(response["interface_id"], const.ADMIN_INTERFACE_ID)
                self.assertEqual(
                    response["interface_version"], const.ADMIN_INTERFACE_VERSION
                )
                self.assertEqual(response["schema_id"], const.SCHEMA_ID)
                self.assertEqual(response["schema_version"], const.SCHEMA_VERSION)

            self.assertEqual(results["listed"]["total_count"], 8)
            self.assertEqual(
                results["found"]["normalized_intent_id"], "classic_fm"
            )
            self.assertTrue(results["validated_record"]["valid"])
            self.assertTrue(results["validated_candidate"]["valid"])
            self.assertFalse(draft_path.exists())
            self.assertEqual(results["activated"]["active_count"], 9)
            self.assertEqual(
                results["activated"]["active_revision"],
                results["activated"]["persisted_revision"],
            )
            self.assertEqual(
                results["activated_record"]["record"]["title"], "Evening"
            )
            self.assertEqual(results["final_status"]["draft_state"], "absent")
            self.assertFalse(results["final_status"]["activation_required"])

    def test_advnfc_is_optional_and_no_tag_assignments_are_stored(self) -> None:
        capabilities = administration.AdministrationManager.capabilities()
        advertised = json.dumps(capabilities, sort_keys=True).lower()
        self.assertNotIn("advnfc", advertised)
        self.assertNotIn("tag_mapping", advertised)

        runtime_source = "\n".join(
            (INTEGRATION / name).read_text(encoding="utf-8")
            for name in ("__init__.py", "administration.py", "catalogue.py", "const.py")
        ).lower()
        self.assertNotIn("advnfc", runtime_source)
        self.assertNotIn("tag_mapping", runtime_source)

        active = _load(FIXTURES / "valid" / "current_baseline_migrated.yaml")
        serialized = json.dumps(catalogue.registry_document(active), sort_keys=True)
        self.assertNotIn("uid", serialized)
        self.assertNotIn("tag_mapping", serialized)

        contract = (
            ROOT / "03_Contracts" / "ASTV_INTENT_CATALOGUE_ADMINISTRATION_INTERFACE.md"
        ).read_text(encoding="utf-8")
        self.assertIn("AdvNFC owns stored NFC mappings", contract)
        self.assertIn("No matches is a successful empty AdvNFC result", contract)


class PackagingAndAdapterTests(unittest.TestCase):
    def test_manifest_and_hacs_metadata(self) -> None:
        manifest = json.loads((INTEGRATION / "manifest.json").read_text())
        hacs = json.loads((ROOT / "hacs.json").read_text())
        self.assertEqual(manifest["domain"], const.DOMAIN)
        self.assertEqual(manifest["version"], "0.5.0")
        self.assertEqual(manifest["dependencies"], ["frontend", "http", "panel_custom"])
        self.assertTrue(manifest["config_flow"])
        self.assertTrue(manifest["single_config_entry"])
        self.assertEqual(hacs, {"name": "ASTV Intent Catalogue"})
        self.assertTrue((INTEGRATION / "brand" / "icon.png").is_file())

    def test_panel_registration_uses_bundled_hashed_module_and_read_visibility(self) -> None:
        hass = FakeHass()
        asyncio.run(integration.async_setup(hass, {}))

        self.assertEqual(len(hass.http.paths), 1)
        static_path = hass.http.paths[0]
        self.assertEqual(static_path.url_path, const.PANEL_STATIC_URL)
        self.assertTrue(static_path.cache_headers)
        self.assertEqual(Path(static_path.path), INTEGRATION / "frontend")

        panel = hass.panels[const.PANEL_URL_PATH]
        self.assertEqual(panel["webcomponent_name"], const.PANEL_WEB_COMPONENT)
        self.assertFalse(panel["embed_iframe"])
        self.assertFalse(panel["require_admin"])
        self.assertTrue(panel["handle_safe_area"])
        self.assertRegex(
            panel["module_url"],
            rf"^{const.PANEL_STATIC_URL}/{const.PANEL_MODULE}\?v=[0-9a-f]{{16}}$",
        )
        self.assertEqual(
            panel["config"], {"interface_version": const.ADMIN_INTERFACE_VERSION}
        )

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

        gateway_sequence = script_definitions["astv_intent_gateway"]["sequence"]
        self.assertEqual(
            gateway_sequence[0]["action"], "script.astv_find_intent_record"
        )
        gateway_text = json.dumps(gateway_sequence)
        self.assertIn("No Intent Record Found", gateway_text)
        self.assertIn("script.astv_resolve_area", gateway_text)
        self.assertIn("script.astv_select_intent_engine", gateway_text)

    def test_supported_gateway_negative_paths_stop_before_internal_routing(self) -> None:
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

        class HomeAssistantYamlLoader(yaml.SafeLoader):
            pass

        HomeAssistantYamlLoader.add_constructor(
            "!include", lambda loader, node: loader.construct_scalar(node)
        )
        document = yaml.load(
            scripts_path.read_text(encoding="utf-8"),
            Loader=HomeAssistantYamlLoader,
        )
        gateway_sequence = document["script"]["astv_intent_gateway"]["sequence"]

        missing_record_guard = gateway_sequence[1]
        self.assertIn("count == 0", missing_record_guard["if"][0]["value_template"])
        self.assertEqual(
            missing_record_guard["then"][-1],
            {"stop": "No intent record found", "error": False},
        )
        self.assertNotIn(
            "script.astv_select_intent_engine", json.dumps(missing_record_guard)
        )

        unresolved_area_guard = gateway_sequence[4]
        self.assertIn(
            "target_area == ''", unresolved_area_guard["if"][0]["value_template"]
        )
        self.assertEqual(
            unresolved_area_guard["then"][-1],
            {"stop": "No target area resolved", "error": False},
        )
        self.assertNotIn(
            "script.astv_select_intent_engine", json.dumps(unresolved_area_guard)
        )

        self.assertEqual(
            gateway_sequence[-1]["action"], "script.astv_select_intent_engine"
        )


if __name__ == "__main__":
    unittest.main()
