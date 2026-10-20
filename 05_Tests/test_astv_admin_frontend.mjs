import assert from "node:assert/strict";
import test from "node:test";

globalThis.HTMLElement = class {};

const {
  ASTVAdapterError,
  ASTVIntentCataloguePanel,
  ASTVProviderAdapter,
  blankIntentRecord,
  filterAndSortIntents,
  validateIntentEntry,
} = await import("../custom_components/astv_intent_catalogue/frontend/astv-intent-catalogue-panel.mjs");

function hassWith(handler, isAdmin = false) {
  return {
    user: { is_admin: isAdmin },
    callWS: async (message) => handler(message),
  };
}

test("response-only calls use the authenticated Home Assistant WebSocket envelope", async () => {
  let observed;
  const adapter = new ASTVProviderAdapter(hassWith(async (message) => {
    observed = message;
    return {
      context: { id: "ctx" },
      response: {
        ok: true,
        interface_id: "astv.intent_catalogue.administration",
        interface_version: "1.1.0",
        capabilities: ["discovery"],
      },
    };
  }));

  const response = await adapter.discover();
  assert.equal(response.ok, true);
  assert.deepEqual(observed, {
    type: "call_service",
    domain: "astv_intent_catalogue",
    service: "get_administration_capabilities",
    service_data: {},
    return_response: true,
  });
});

test("native Home Assistant errors retain their code and transport classification", async () => {
  const adapter = new ASTVProviderAdapter(hassWith(async () => {
    throw { code: "unauthorized", message: "Unauthorized" };
  }));

  await assert.rejects(
    adapter.status(),
    (error) => error instanceof ASTVAdapterError
      && error.kind === "transport"
      && error.code === "unauthorized",
  );
});

test("timeout is visible and does not become a provider outcome", async () => {
  const adapter = new ASTVProviderAdapter(
    hassWith(() => new Promise(() => {})),
    { timeoutMs: 5 },
  );
  await assert.rejects(
    adapter.status(),
    (error) => error.kind === "timeout" && error.code === "timeout",
  );
});

test("non-admin clients cannot initiate manage calls", async () => {
  let called = false;
  const adapter = new ASTVProviderAdapter(hassWith(async () => {
    called = true;
    return {};
  }));
  await assert.rejects(
    adapter.call("create", {}),
    (error) => error.kind === "permission" && error.code === "permission_denied",
  );
  assert.equal(called, false);
});

test("guarded mutation refreshes status and draft after stale revision without retry", async () => {
  const calls = [];
  const adapter = new ASTVProviderAdapter(hassWith(async (message) => {
    calls.push(message);
    const response = message.service === "get_administration_capabilities"
      ? {
          ok: true,
          interface_id: "astv.intent_catalogue.administration",
          interface_version: "1.1.0",
          capabilities: ["draft.create", "draft.list"],
        }
      : message.service === "get_administration_status"
      ? {
          ok: true,
          interface_id: "astv.intent_catalogue.administration",
          interface_version: "1.1.0",
          editable_revision: calls.filter((call) => call.service === "get_administration_status").length === 1 ? "rev-old" : "rev-new",
        }
      : message.service === "create_intent_record"
        ? { ok: false, error: { code: "stale_revision" } }
        : { ok: true, view: "draft", source_revision: "rev-new", records: [] };
    return { context: {}, response };
  }, true));

  const result = await adapter.guardedMutation("create", {
    intent_id: "evening",
    record: { intent: "routine.run", title: "Evening", params: {}, routine: "evening" },
  });

  assert.equal(result.conflict, true);
  assert.equal(calls.filter((call) => call.service === "create_intent_record").length, 1);
  const createCall = calls.find((call) => call.service === "create_intent_record");
  assert.equal(createCall.service_data.expected_revision, "rev-old");
  assert.equal(result.refreshed_status.editable_revision, "rev-new");
  assert.equal(result.refreshed_view.view, "draft");
});

test("draft view is negotiated and never probed against a provider that does not advertise it", async () => {
  const calls = [];
  const adapter = new ASTVProviderAdapter(hassWith(async (message) => {
    calls.push(message);
    return {
      context: {},
      response: {
        ok: true,
        interface_id: "astv.intent_catalogue.administration",
        interface_version: "1.0.0",
        capabilities: ["active.list"],
      },
    };
  }));
  await assert.rejects(
    adapter.list("draft"),
    (error) => error.kind === "provider" && error.code === "unsupported_capability",
  );
  assert.deepEqual(calls.map((call) => call.service), ["get_administration_capabilities"]);
});

test("optional AdvNFC absence is isolated from ASTV editing", async () => {
  const adapter = new ASTVProviderAdapter(hassWith(async (message) => {
    if (message.domain === "advnfc") throw { code: "not_found", message: "Service missing" };
    throw new Error("unexpected call");
  }));
  assert.deepEqual(await adapter.queryAdvNfc("classic_fm"), {
    available: false,
    mappings: [],
    reason: "provider_unavailable",
  });
});

test("listAll follows provider pagination without mixing revisions", async () => {
  const cursors = [];
  const adapter = new ASTVProviderAdapter(hassWith(async (message) => {
    if (message.service === "get_administration_capabilities") {
      return { context: {}, response: { ok: true, interface_id: "astv.intent_catalogue.administration", interface_version: "1.1.0", capabilities: ["active.list"] } };
    }
    cursors.push(message.service_data.cursor ?? null);
    const second = message.service_data.cursor === "page-2";
    return { context: {}, response: { ok: true, active_revision: "rev-a", records: [{ intent_id: second ? "two" : "one", record: blankIntentRecord("routine.run") }], next_cursor: second ? null : "page-2" } };
  }));

  const result = await adapter.listAll("active");
  assert.deepEqual(cursors, [null, "page-2"]);
  assert.deepEqual(result.records.map((entry) => entry.intent_id), ["one", "two"]);
});

test("client validation preserves schema v1 shapes and rejects non-canonical fields", () => {
  const media = blankIntentRecord();
  media.title = "Classic FM";
  media.params.output.domain = "audio";
  media.params.catalogue_id = "curated_media";
  media.params.item_id = "classic-fm";
  assert.deepEqual(validateIntentEntry({ intentId: "classic_fm", record: media }), {});
  assert.equal(Object.hasOwn(media, "description"), false);

  const routine = blankIntentRecord("routine.run");
  routine.title = "Morning";
  routine.routine = "Morning Routine";
  assert.equal(validateIntentEntry({ intentId: "Morning", record: routine }).intentId.length > 0, true);
  assert.equal(validateIntentEntry({ intentId: "morning", record: routine }).routine.length > 0, true);
});

test("intent list searches ID and Name, filters supported type, and sorts", () => {
  const entries = [
    { intentId: "z_radio", record: { intent: "media.play_source", title: "Classic FM" } },
    { intentId: "alarm", record: { intent: "routine.run", title: "Morning routine" } },
  ];
  assert.deepEqual(filterAndSortIntents(entries, { search: "classic" }).map((entry) => entry.intentId), ["z_radio"]);
  assert.deepEqual(filterAndSortIntents(entries, { type: "routine.run" }).map((entry) => entry.intentId), ["alarm"]);
  assert.deepEqual(filterAndSortIntents(entries, { sort: "name-desc" }).map((entry) => entry.intentId), ["alarm", "z_radio"]);
});

test("Home Assistant state updates preserve the mounted panel DOM", () => {
  const panel = Object.create(ASTVIntentCataloguePanel.prototype);
  let rendered = 0;
  let observedHass;
  panel.initialized = true;
  panel.adapter = { setHass(value) { observedHass = value; } };
  panel.render = () => { rendered += 1; };
  const nextHass = { user: { is_admin: true }, states: { changed: {} } };

  panel.hass = nextHass;

  assert.equal(panel._hass, nextHass);
  assert.equal(observedHass, nextHass);
  assert.equal(rendered, 0);
});

test("search input updates list rows in place without replacing the focused control", () => {
  const listeners = {};
  const search = { value: "", addEventListener(type, listener) { listeners[type] = listener; } };
  const table = { innerHTML: "" };
  const resultCount = { textContent: "" };
  const wrap = { scrollTop: 19 };
  const root = {
    querySelector(selector) {
      return {
        "[data-action=add]": null,
        "[name=search]": search,
        "[name=type]": null,
        "[name=sort]": null,
        ".intent-table": table,
        ".result-count": resultCount,
        ".table-wrap": wrap,
      }[selector];
    },
    querySelectorAll() { return []; },
  };
  const panel = Object.create(ASTVIntentCataloguePanel.prototype);
  Object.assign(panel, {
    shadowRoot: root,
    screen: "list",
    filters: { search: "", type: "all", sort: "id-asc" },
    records: [
      { intentId: "classic_fm", record: { intent: "media.play_source", title: "Classic FM" } },
      { intentId: "morning", record: { intent: "routine.run", title: "Morning" } },
    ],
    tagCounts: new Map(),
    listScrollTop: 19,
    render() { throw new Error("search must not perform a full render"); },
  });

  panel.bindListEvents();
  listeners.input({ target: { value: "classic" } });

  assert.equal(root.querySelector("[name=search]"), search);
  assert.equal(panel.filters.search, "classic");
  assert.equal(resultCount.textContent, "1 of 2 intents");
  assert.match(table.innerHTML, /classic_fm/);
  assert.doesNotMatch(table.innerHTML, /morning/);
  assert.equal(wrap.scrollTop, 0);
});
