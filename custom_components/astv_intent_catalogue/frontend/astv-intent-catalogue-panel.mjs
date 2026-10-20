const ASTV_DOMAIN = "astv_intent_catalogue";
const ASTV_INTERFACE_ID = "astv.intent_catalogue.administration";
const ADVNFC_DOMAIN = "advnfc";
const ADVNFC_INTERFACE_ID = "advnfc.tag_mapping.administration";

const OPERATIONS = Object.freeze({
  capabilities: "get_administration_capabilities",
  status: "get_administration_status",
  list: "list_intent_records",
  get: "get_intent_record",
  validateRecord: "validate_intent_record",
  validateCandidate: "validate_intent_catalogue",
  create: "create_intent_record",
  update: "update_intent_record",
  delete: "delete_intent_record",
  discard: "discard_intent_catalogue_draft",
  activate: "activate_intent_catalogue",
});

const MANAGE_OPERATIONS = new Set([
  "validateRecord",
  "validateCandidate",
  "create",
  "update",
  "delete",
  "discard",
  "activate",
]);

const OPERATION_CAPABILITIES = Object.freeze({
  validateRecord: "validation.record",
  validateCandidate: "validation.candidate",
  create: "draft.create",
  update: "draft.update",
  delete: "draft.delete",
  discard: "draft.discard",
  activate: "activation.explicit",
});

export class ASTVAdapterError extends Error {
  constructor(kind, code, message, cause = undefined) {
    super(message);
    this.name = "ASTVAdapterError";
    this.kind = kind;
    this.code = code;
    this.cause = cause;
  }
}

function nativeCode(error) {
  return String(error?.code ?? error?.error?.code ?? "unknown_error");
}

function nativeMessage(error) {
  return String(error?.message ?? error?.error?.message ?? "Home Assistant request failed");
}

export class ASTVProviderAdapter {
  constructor(hass, { timeoutMs = 15000 } = {}) {
    this.hass = hass;
    this.timeoutMs = timeoutMs;
    this.capabilities = null;
  }

  setHass(hass) {
    this.hass = hass;
  }

  get canManage() {
    return this.hass?.user?.is_admin === true;
  }

  async call(operation, serviceData = {}) {
    const service = OPERATIONS[operation];
    if (!service) {
      throw new ASTVAdapterError("client", "unsupported_operation", `Unsupported operation: ${operation}`);
    }
    if (MANAGE_OPERATIONS.has(operation) && !this.canManage) {
      throw new ASTVAdapterError("permission", "permission_denied", "Administrator access is required.");
    }
    return this.callService(ASTV_DOMAIN, service, serviceData);
  }

  async callService(domain, service, serviceData = {}) {
    if (!this.hass?.callWS) {
      throw new ASTVAdapterError("client", "connection_unavailable", "Home Assistant WebSocket is unavailable.");
    }

    let timer;
    const timeout = new Promise((_, reject) => {
      timer = globalThis.setTimeout(
        () => reject(new ASTVAdapterError("timeout", "timeout", `Timed out calling ${domain}.${service}.`)),
        this.timeoutMs,
      );
    });

    try {
      const result = await Promise.race([
        this.hass.callWS({
          type: "call_service",
          domain,
          service,
          service_data: serviceData,
          return_response: true,
        }),
        timeout,
      ]);
      if (!result || typeof result.response !== "object" || result.response === null) {
        throw new ASTVAdapterError("transport", "invalid_response", `${domain}.${service} returned no response payload.`);
      }
      return result.response;
    } catch (error) {
      if (error instanceof ASTVAdapterError) {
        throw error;
      }
      throw new ASTVAdapterError("transport", nativeCode(error), nativeMessage(error), error);
    } finally {
      globalThis.clearTimeout(timer);
    }
  }

  async discover() {
    const response = await this.call("capabilities");
    if (!response.ok || response.interface_id !== ASTV_INTERFACE_ID || !String(response.interface_version ?? "").startsWith("1.")) {
      throw new ASTVAdapterError("provider", "incompatible_interface", "The installed ASTV administration interface is not compatible.");
    }
    this.capabilities = response;
    return response;
  }

  async requireCapability(capability) {
    const discovery = this.capabilities ?? await this.discover();
    if (!Array.isArray(discovery.capabilities) || !discovery.capabilities.includes(capability)) {
      throw new ASTVAdapterError("provider", "unsupported_capability", `The installed provider does not advertise ${capability}.`);
    }
    return discovery;
  }

  status() {
    return this.call("status");
  }

  async list(view = "active", { limit = 100, cursor = undefined } = {}) {
    await this.requireCapability(view === "draft" ? "draft.list" : "active.list");
    const data = { view, limit };
    if (cursor !== undefined && cursor !== null) data.cursor = cursor;
    return this.call("list", data);
  }

  async get(intentId, view = "active") {
    await this.requireCapability(view === "draft" ? "draft.get" : "active.get");
    return this.call("get", { intent_id: intentId, view });
  }

  async guardedMutation(operation, payload = {}, refreshView = "draft") {
    if (!MANAGE_OPERATIONS.has(operation)) {
      throw new ASTVAdapterError("client", "unsupported_mutation", `Not a mutation operation: ${operation}`);
    }
    await this.requireCapability(OPERATION_CAPABILITIES[operation]);
    const status = await this.status();
    if (!status.ok || !status.editable_revision) return status;

    const result = await this.call(operation, {
      ...payload,
      expected_revision: status.editable_revision,
    });
    if (result?.ok !== false || result?.error?.code !== "stale_revision") return result;

    const refreshedStatus = await this.status();
    const refreshedView = await this.list(refreshView).catch((error) => ({
      ok: false,
      error: { code: error.code, message: error.message },
    }));
    return {
      ok: false,
      conflict: true,
      result,
      refreshed_status: refreshedStatus,
      refreshed_view: refreshedView,
    };
  }

  activate() {
    return this.guardedMutation("activate");
  }

  discard() {
    return this.guardedMutation("discard", {}, "active");
  }

  async queryAdvNfc(intentId) {
    let capabilities;
    try {
      capabilities = await this.callService(ADVNFC_DOMAIN, "get_administration_capabilities");
    } catch (error) {
      if (error instanceof ASTVAdapterError && ["not_found", "service_not_found", "unknown_command"].includes(error.code)) {
        return { available: false, mappings: [], reason: "provider_unavailable" };
      }
      throw error;
    }
    if (capabilities.interface_id !== ADVNFC_INTERFACE_ID || !capabilities.ok) {
      return { available: false, mappings: [], reason: "incompatible_provider" };
    }
    const response = await this.callService(ADVNFC_DOMAIN, "query_tag_mappings", {
      action_type: "astv_intent",
      intent_id: intentId,
    });
    return response.ok
      ? { available: true, mappings: response.mappings ?? [], response }
      : { available: true, mappings: [], response };
  }
}

export class ASTVIntentCataloguePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.adapter = null;
    this.busy = false;
  }

  set hass(value) {
    this._hass = value;
    if (!this.adapter) this.adapter = new ASTVProviderAdapter(value);
    else this.adapter.setHass(value);
    this.render();
    const permission = this.shadowRoot?.querySelector(".permission");
    if (permission) permission.textContent = `Read access: available · Manage access: ${this.adapter.canManage ? "administrator" : "read only"}`;
  }

  set panel(value) {
    this._panel = value;
  }

  async run(operation) {
    if (this.busy) return;
    this.busy = true;
    this.renderStatus("Loading…", "loading");
    this.toggleButtons(true);
    try {
      const response = operation === "capabilities"
        ? await this.adapter.discover()
        : operation === "status"
          ? await this.adapter.status()
          : await this.adapter.list(operation);
      this.renderStatus(JSON.stringify(response, null, 2), response.ok ? "success" : "error");
    } catch (error) {
      this.renderStatus(`${error.code ?? "error"}: ${error.message}`, "error");
    } finally {
      this.busy = false;
      this.toggleButtons(false);
    }
  }

  toggleButtons(disabled) {
    this.shadowRoot?.querySelectorAll("button").forEach((button) => { button.disabled = disabled; });
  }

  renderStatus(text, state = "idle") {
    const output = this.shadowRoot?.querySelector("pre");
    if (!output) return;
    output.textContent = text;
    output.dataset.state = state;
  }

  render() {
    if (!this.shadowRoot || !this._hass || this.shadowRoot.childElementCount) return;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; min-height: 100%; color: var(--primary-text-color); background: var(--primary-background-color); }
        main { box-sizing: border-box; max-width: 62rem; margin: 0 auto; padding: max(1rem, env(safe-area-inset-top)) max(1rem, env(safe-area-inset-right)) max(1rem, env(safe-area-inset-bottom)) max(1rem, env(safe-area-inset-left)); }
        h1 { font-size: clamp(1.35rem, 5vw, 2rem); margin: 0 0 .35rem; }
        p { line-height: 1.45; }
        .permission { color: var(--secondary-text-color); }
        .actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr)); gap: .75rem; margin: 1rem 0; }
        button { min-height: 2.75rem; border: 0; border-radius: .4rem; padding: .65rem .85rem; color: var(--text-primary-color, white); background: var(--primary-color); font: inherit; cursor: pointer; }
        button:disabled { opacity: .55; cursor: progress; }
        pre { min-height: 10rem; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; padding: 1rem; border-radius: .5rem; background: var(--card-background-color); box-shadow: var(--ha-card-box-shadow, none); }
        pre[data-state="error"] { border-inline-start: .3rem solid var(--error-color); }
        pre[data-state="success"] { border-inline-start: .3rem solid var(--success-color, #2e7d32); }
        @media (max-width: 420px) { main { padding-inline: .75rem; } .actions { grid-template-columns: 1fr 1fr; } }
      </style>
      <main>
        <h1>ASTV Intent Catalogue</h1>
        <p>Transport proof for provider-owned active and durable draft reads. It does not edit or activate catalogue state.</p>
        <p class="permission">Read access: available · Manage access: ${this.adapter.canManage ? "administrator" : "read only"}</p>
        <div class="actions">
          <button data-operation="capabilities">Capabilities</button>
          <button data-operation="status">Status</button>
          <button data-operation="active">Active records</button>
          <button data-operation="draft">Draft records</button>
        </div>
        <pre aria-live="polite">Choose a proof operation.</pre>
      </main>`;
    this.shadowRoot.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => this.run(button.dataset.operation));
    });
  }
}

if (globalThis.customElements && !globalThis.customElements.get("astv-intent-catalogue-panel")) {
  globalThis.customElements.define("astv-intent-catalogue-panel", ASTVIntentCataloguePanel);
}
