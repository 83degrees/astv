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
    state: "unavailable",
    mappings: [],
    reason: "provider_unavailable",
  });
});

test("AdvNFC reverse lookup negotiates v3 query capability and normalizes populated results", async () => {
  const calls = [];
  const adapter = new ASTVProviderAdapter(hassWith(async (message) => {
    calls.push(message);
    const response = message.service === "get_administration_capabilities"
      ? { ok: true, interface_id: "advnfc.tag_mapping.administration", interface_version: "3.0.0", operations: ["query"] }
      : { ok: true, mappings: [{ uid: "04A1", label: "Kitchen", action: { type: "astv_intent", intent_id: "classic_fm" } }] };
    return { context: {}, response };
  }));

  const result = await adapter.queryAdvNfc("classic_fm");

  assert.equal(result.state, "populated");
  assert.equal(result.available, true);
  assert.equal(result.mappings[0].uid, "04A1");
  assert.deepEqual(calls.map((call) => call.service), ["get_administration_capabilities", "query_tag_mappings"]);
  assert.deepEqual(calls[1].service_data, { action_type: "astv_intent", intent_id: "classic_fm" });
});

test("AdvNFC incompatibility is isolated and does not probe the query operation", async () => {
  const calls = [];
  const adapter = new ASTVProviderAdapter(hassWith(async (message) => {
    calls.push(message);
    return { context: {}, response: { ok: true, interface_id: "advnfc.tag_mapping.administration", interface_version: "2", operations: ["query"] } };
  }));

  const result = await adapter.queryAdvNfc("classic_fm");

  assert.equal(result.state, "incompatible");
  assert.equal(result.available, false);
  assert.deepEqual(calls.map((call) => call.service), ["get_administration_capabilities"]);
});

test("AdvNFC authorization and query errors remain distinguishable", async () => {
  const unauthorized = new ASTVProviderAdapter(hassWith(async () => {
    throw { code: "unauthorized", message: "Unauthorized" };
  }));
  assert.equal((await unauthorized.queryAdvNfc("classic_fm")).state, "unauthorized");

  const failed = new ASTVProviderAdapter(hassWith(async (message) => ({
    context: {},
    response: message.service === "get_administration_capabilities"
      ? { ok: true, interface_id: "advnfc.tag_mapping.administration", interface_version: 3, operations: ["query"] }
      : { ok: false, error: { code: "provider_failed", message: "Query failed" } },
  })));
  assert.equal((await failed.queryAdvNfc("classic_fm")).state, "error");

  const unavailable = new ASTVProviderAdapter(hassWith(async () => ({
    context: {}, response: { ok: false, error: { code: "dependency_unavailable", message: "Provider unavailable" } },
  })));
  assert.equal((await unavailable.queryAdvNfc("classic_fm")).state, "unavailable");
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

test("known AdvNFC references block ASTV deletion before mutation", async () => {
  let mutated = false;
  const panel = Object.create(ASTVIntentCataloguePanel.prototype);
  Object.assign(panel, {
    adapter: {
      canManage: true,
      async queryAdvNfc() { return { available: true, state: "populated", mappings: [{ uid: "04A1", label: "Kitchen" }] }; },
      async guardedMutation() { mutated = true; return { ok: true }; },
    },
    view: "draft",
    status: { draft_state: "valid" },
    original: { intentId: "classic_fm" },
    associations: new Map(),
    busy: false,
    render() {},
  });

  await panel.deleteEditor();

  assert.equal(mutated, false);
  assert.equal(panel.notice.kind, "warning");
  assert.match(panel.notice.text, /Kitchen \(04A1\)/);
});

test("unknown optional association state warns but does not hard-block confirmed deletion", async () => {
  const priorConfirm = globalThis.confirm;
  globalThis.confirm = () => true;
  let mutated = 0;
  const panel = Object.create(ASTVIntentCataloguePanel.prototype);
  Object.assign(panel, {
    adapter: {
      canManage: true,
      async queryAdvNfc() { return { available: false, state: "unavailable", mappings: [] }; },
      async guardedMutation() { mutated += 1; return { ok: true }; },
      async status() { return { ok: true, draft_state: "valid" }; },
    },
    view: "draft",
    status: { draft_state: "valid" },
    original: { intentId: "classic_fm" },
    associations: new Map(),
    busy: false,
    render() {},
    async loadRecords() {},
  });
  try {
    await panel.deleteEditor();
  } finally {
    globalThis.confirm = priorConfirm;
  }

  assert.equal(mutated, 1);
  assert.equal(panel.notice.kind, "success");
});

test("Status tab keeps Save and explicit activation semantically separate", () => {
  const panel = Object.create(ASTVIntentCataloguePanel.prototype);
  Object.assign(panel, {
    adapter: { canManage: true },
    section: "status",
    busy: false,
    notice: null,
    status: {
      provider_state: "available",
      active_state: "available",
      persisted_state: "valid",
      draft_state: "valid",
      active_revision: "rev-active",
      persisted_revision: "rev-active",
      draft_revision: "rev-draft",
      editable_revision: "rev-draft",
      activation_required: true,
      schema_version: "1.0.0",
      last_activation_error: null,
    },
  });

  const html = panel.renderStatus();
  assert.match(html, /Activate shared draft/);
  assert.match(html, /Save stages changes only/);
  assert.match(html, /rev-active/);
  assert.match(html, /rev-draft/);
});

test("Tags tab renders safe provider identifiers and isolates unavailable associations", () => {
  const panel = Object.create(ASTVIntentCataloguePanel.prototype);
  Object.assign(panel, {
    adapter: { canManage: false },
    section: "tags",
    busy: false,
    notice: null,
    records: [
      { intentId: "classic_fm", record: { title: "Classic <FM>" } },
      { intentId: "morning", record: { title: "Morning" } },
    ],
    associations: new Map([
      ["classic_fm", { available: true, state: "populated", mappings: [{ uid: "04<A1", label: "Kitchen & hall" }] }],
      ["morning", { available: false, state: "unavailable", mappings: [] }],
    ]),
  });

  const html = panel.renderTags();
  assert.match(html, /Classic &lt;FM&gt;/);
  assert.match(html, /04&lt;A1/);
  assert.match(html, /Kitchen &amp; hall/);
  assert.match(html, /AdvNFC is unavailable/);
  assert.doesNotMatch(html, /href=/);
});

test("non-admin Status tab exposes state without an activation control", () => {
  const panel = Object.create(ASTVIntentCataloguePanel.prototype);
  Object.assign(panel, {
    adapter: { canManage: false },
    section: "status",
    busy: false,
    notice: null,
    status: { provider_state: "available", draft_state: "valid", activation_required: true },
  });

  const html = panel.renderStatus();
  assert.match(html, /Read only/);
  assert.doesNotMatch(html, /data-action="activate"/);
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
    associations: new Map(),
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
