import assert from "node:assert/strict";
import test from "node:test";

globalThis.HTMLElement = class {};

const {
  ASTVAdapterError,
  ASTVProviderAdapter,
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
