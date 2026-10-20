const ASTV_DOMAIN = "astv_intent_catalogue";
const ASTV_INTERFACE_ID = "astv.intent_catalogue.administration";
const ADVNFC_DOMAIN = "advnfc";
const ADVNFC_INTERFACE_ID = "advnfc.tag_mapping.administration";
const CANONICAL_ID = /^[a-z0-9][a-z0-9_]*$/;
const MEDIACAT_ID = /^[a-z0-9][a-z0-9_-]*$/;
const SUPPORTED_TYPES = Object.freeze(["media.play_source", "routine.run"]);

const OPERATIONS = Object.freeze({
  capabilities: "get_administration_capabilities", status: "get_administration_status",
  list: "list_intent_records", get: "get_intent_record", validateRecord: "validate_intent_record",
  validateCandidate: "validate_intent_catalogue", create: "create_intent_record",
  update: "update_intent_record", delete: "delete_intent_record",
  discard: "discard_intent_catalogue_draft", activate: "activate_intent_catalogue",
});
const MANAGE_OPERATIONS = new Set(["validateRecord", "validateCandidate", "create", "update", "delete", "discard", "activate"]);
const OPERATION_CAPABILITIES = Object.freeze({
  validateRecord: "validation.record", validateCandidate: "validation.candidate",
  create: "draft.create", update: "draft.update", delete: "draft.delete",
  discard: "draft.discard", activate: "activation.explicit",
});

export class ASTVAdapterError extends Error {
  constructor(kind, code, message, cause = undefined) {
    super(message); this.name = "ASTVAdapterError"; this.kind = kind; this.code = code; this.cause = cause;
  }
}

function nativeCode(error) { return String(error?.code ?? error?.error?.code ?? "unknown_error"); }
function nativeMessage(error) { return String(error?.message ?? error?.error?.message ?? "Home Assistant request failed"); }

export function blankIntentRecord(type = "media.play_source") {
  return type === "routine.run"
    ? { intent: type, title: "", routine: "", params: {} }
    : { intent: "media.play_source", title: "", params: { output: { domain: "" }, catalogue_id: "", item_id: "" } };
}

export function normalizeIntentEntry(intentId, record) {
  const clone = globalThis.structuredClone ? structuredClone(record) : JSON.parse(JSON.stringify(record));
  return { intentId: String(intentId ?? ""), record: clone };
}

export function validateIntentEntry(entry) {
  const errors = {}; const id = String(entry?.intentId ?? ""); const record = entry?.record ?? {};
  const canonical = (value, field, expression = CANONICAL_ID) => {
    if (typeof value !== "string" || !expression.test(value)) errors[field] = "Use a canonical lower-case identifier.";
  };
  canonical(id, "intentId");
  if (typeof record.title !== "string" || record.title.trim() === "") errors.title = "Name is required.";
  if (!SUPPORTED_TYPES.includes(record.intent)) errors.intent = "Choose a supported intent type.";
  if (record.area_override !== undefined) canonical(record.area_override, "areaOverride");
  if (record.intent === "media.play_source") {
    canonical(record.params?.output?.domain, "outputDomain");
    canonical(record.params?.catalogue_id, "catalogueId", MEDIACAT_ID);
    canonical(record.params?.item_id, "itemId", MEDIACAT_ID);
  } else if (record.intent === "routine.run") canonical(record.routine, "routine");
  return errors;
}

export function filterAndSortIntents(entries, { search = "", type = "all", sort = "id-asc" } = {}) {
  const needle = search.trim().toLocaleLowerCase();
  const filtered = entries.filter(({ intentId, record }) => (!needle
    || intentId.toLocaleLowerCase().includes(needle)
    || String(record.title ?? "").toLocaleLowerCase().includes(needle))
    && (type === "all" || record.intent === type));
  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  const [field, direction] = sort.split("-"); const multiplier = direction === "desc" ? -1 : 1;
  return filtered.sort((left, right) => {
    const a = field === "name" ? left.record.title : left.intentId;
    const b = field === "name" ? right.record.title : right.intentId;
    return multiplier * (collator.compare(String(a ?? ""), String(b ?? "")) || collator.compare(left.intentId, right.intentId));
  });
}

export class ASTVProviderAdapter {
  constructor(hass, { timeoutMs = 15000 } = {}) { this.hass = hass; this.timeoutMs = timeoutMs; this.capabilities = null; }
  setHass(hass) { this.hass = hass; }
  get canManage() { return this.hass?.user?.is_admin === true; }

  async call(operation, serviceData = {}) {
    const service = OPERATIONS[operation];
    if (!service) throw new ASTVAdapterError("client", "unsupported_operation", `Unsupported operation: ${operation}`);
    if (MANAGE_OPERATIONS.has(operation) && !this.canManage) throw new ASTVAdapterError("permission", "permission_denied", "Administrator access is required.");
    return this.callService(ASTV_DOMAIN, service, serviceData);
  }

  async callService(domain, service, serviceData = {}) {
    if (!this.hass?.callWS) throw new ASTVAdapterError("client", "connection_unavailable", "Home Assistant WebSocket is unavailable.");
    let timer;
    const timeout = new Promise((_, reject) => { timer = globalThis.setTimeout(() => reject(new ASTVAdapterError("timeout", "timeout", `Timed out calling ${domain}.${service}.`)), this.timeoutMs); });
    try {
      const result = await Promise.race([this.hass.callWS({ type: "call_service", domain, service, service_data: serviceData, return_response: true }), timeout]);
      if (!result || typeof result.response !== "object" || result.response === null) throw new ASTVAdapterError("transport", "invalid_response", `${domain}.${service} returned no response payload.`);
      return result.response;
    } catch (error) {
      if (error instanceof ASTVAdapterError) throw error;
      throw new ASTVAdapterError("transport", nativeCode(error), nativeMessage(error), error);
    } finally { globalThis.clearTimeout(timer); }
  }

  async discover() {
    const response = await this.call("capabilities");
    if (!response.ok || response.interface_id !== ASTV_INTERFACE_ID || !String(response.interface_version ?? "").startsWith("1.")) throw new ASTVAdapterError("provider", "incompatible_interface", "The installed ASTV administration interface is not compatible.");
    this.capabilities = response; return response;
  }
  async requireCapability(capability) {
    const discovery = this.capabilities ?? await this.discover();
    if (!Array.isArray(discovery.capabilities) || !discovery.capabilities.includes(capability)) throw new ASTVAdapterError("provider", "unsupported_capability", `The installed provider does not advertise ${capability}.`);
    return discovery;
  }
  status() { return this.call("status"); }
  async list(view = "active", { limit = 100, cursor = undefined } = {}) {
    await this.requireCapability(view === "draft" ? "draft.list" : "active.list");
    const data = { view, limit }; if (cursor != null) data.cursor = cursor; return this.call("list", data);
  }
  async listAll(view = "active") {
    const records = []; let cursor; let identity;
    do {
      const response = await this.list(view, { limit: 200, cursor });
      if (!response.ok) return response;
      const nextIdentity = response.source_revision ?? response.active_revision;
      if (identity !== undefined && identity !== nextIdentity) throw new ASTVAdapterError("provider", "stale_cursor", "The selected catalogue changed while loading.");
      identity = nextIdentity; records.push(...(response.records ?? [])); cursor = response.next_cursor;
    } while (cursor);
    return { ok: true, view, source_revision: identity, records, total_count: records.length };
  }
  async get(intentId, view = "active") { await this.requireCapability(view === "draft" ? "draft.get" : "active.get"); return this.call("get", { intent_id: intentId, view }); }
  async guardedMutation(operation, payload = {}, refreshView = "draft") {
    if (!MANAGE_OPERATIONS.has(operation)) throw new ASTVAdapterError("client", "unsupported_mutation", `Not a mutation operation: ${operation}`);
    await this.requireCapability(OPERATION_CAPABILITIES[operation]);
    const status = await this.status(); if (!status.ok || !status.editable_revision) return status;
    const result = await this.call(operation, { ...payload, expected_revision: status.editable_revision });
    if (result?.ok !== false || result?.error?.code !== "stale_revision") return result;
    const refreshedStatus = await this.status();
    const refreshedView = await this.listAll(refreshView).catch((error) => ({ ok: false, error: { code: error.code, message: error.message } }));
    return { ok: false, conflict: true, result, refreshed_status: refreshedStatus, refreshed_view: refreshedView };
  }
  activate() { return this.guardedMutation("activate"); }
  discard() { return this.guardedMutation("discard", {}, "active"); }
  async queryAdvNfc(intentId) {
    let capabilities;
    try { capabilities = await this.callService(ADVNFC_DOMAIN, "get_administration_capabilities"); }
    catch (error) {
      if (error instanceof ASTVAdapterError && ["not_found", "service_not_found", "unknown_command"].includes(error.code)) return { available: false, mappings: [], reason: "provider_unavailable" };
      throw error;
    }
    if (capabilities.interface_id !== ADVNFC_INTERFACE_ID || !capabilities.ok) return { available: false, mappings: [], reason: "incompatible_provider" };
    const response = await this.callService(ADVNFC_DOMAIN, "query_tag_mappings", { action_type: "astv_intent", intent_id: intentId });
    return response.ok ? { available: true, mappings: response.mappings ?? [], response } : { available: true, mappings: [], response };
  }
}

function escapeHtml(value) { return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;"); }
function errorText(result, fallback) { return result?.error?.message ?? result?.message ?? fallback; }

export class ASTVIntentCataloguePanel extends HTMLElement {
  constructor() {
    super(); this.attachShadow({ mode: "open" }); this.adapter = null; this.busy = false; this.initialized = false;
    this.screen = "list"; this.view = "active"; this.records = []; this.status = null;
    this.filters = { search: "", type: "all", sort: "id-asc" }; this.tagCounts = new Map(); this.listScrollTop = 0;
    this.editing = null; this.original = null; this.editorErrors = {}; this.notice = null;
    this.beforeUnload = (event) => { if (this.isDirty()) { event.preventDefault(); event.returnValue = ""; } };
  }
  set hass(value) {
    this._hass = value;
    if (!this.adapter) this.adapter = new ASTVProviderAdapter(value); else this.adapter.setHass(value);
    if (!this.initialized) void this.initialize();
  }
  set panel(value) { this._panel = value; }
  connectedCallback() { globalThis.addEventListener?.("beforeunload", this.beforeUnload); }
  disconnectedCallback() { globalThis.removeEventListener?.("beforeunload", this.beforeUnload); }

  async initialize() {
    if (!this._hass || this.busy) return; this.busy = true; this.render();
    try {
      const discovery = await this.adapter.discover(); this.status = await this.adapter.status();
      this.view = this.status?.draft_state === "valid" && discovery.capabilities?.includes("draft.list") ? "draft" : "active";
      await this.loadRecords(this.view, false); this.initialized = true;
    }
    catch (error) { this.notice = { kind: "error", text: `${error.code ?? "error"}: ${error.message}` }; }
    finally { this.busy = false; this.render(); }
  }
  async loadRecords(view = this.view, showBusy = true) {
    if (showBusy) { this.busy = true; this.render(); }
    try {
      const response = await this.adapter.listAll(view);
      if (!response.ok) {
        if (view === "draft" && response.error?.refinement === "draft_not_found") { this.view = "active"; return this.loadRecords("active", false); }
        throw new ASTVAdapterError("provider", response.error?.code ?? "provider_error", errorText(response, "Unable to load catalogue."));
      }
      this.view = view; this.records = response.records.map(({ intent_id: id, record }) => normalizeIntentEntry(id, record)); this.tagCounts = new Map(); void this.loadTagCounts(this.records);
    } catch (error) { this.notice = { kind: "error", text: `${error.code ?? "error"}: ${error.message}` }; }
    finally { if (showBusy) { this.busy = false; this.render(); } }
  }
  async loadTagCounts(entries) {
    await Promise.all(entries.map(async ({ intentId }) => {
      try { const result = await this.adapter.queryAdvNfc(intentId); this.tagCounts.set(intentId, result.available ? result.mappings.length : null); }
      catch { this.tagCounts.set(intentId, null); }
    }));
    if (this.screen === "list") this.updateListResults();
  }
  isDirty() { return this.screen === "editor" && JSON.stringify(this.editing) !== JSON.stringify(this.original); }
  canEditCurrentView() { return this.adapter.canManage && (this.view === "draft" || this.status?.draft_state !== "valid"); }
  confirmLeave() { return !this.isDirty() || globalThis.confirm?.("Discard unsaved changes?") !== false; }
  openEditor(entry = null) {
    this.listScrollTop = this.shadowRoot?.querySelector(".table-wrap")?.scrollTop ?? this.listScrollTop;
    this.editing = entry ? normalizeIntentEntry(entry.intentId, entry.record) : { intentId: "", record: blankIntentRecord() };
    this.original = entry ? normalizeIntentEntry(entry.intentId, entry.record) : { intentId: "", record: blankIntentRecord() };
    this.editorErrors = {}; this.notice = null; this.screen = "editor"; this.render();
  }
  closeEditor() { if (!this.confirmLeave()) return; this.screen = "list"; this.editing = null; this.original = null; this.editorErrors = {}; this.render(); }
  updateEditorFromForm(form) {
    const data = new FormData(form); const type = String(data.get("intent")); const record = blankIntentRecord(type);
    record.title = String(data.get("title") ?? ""); const area = String(data.get("area_override") ?? ""); if (area) record.area_override = area;
    if (type === "media.play_source") { record.params.output.domain = String(data.get("output_domain") ?? ""); record.params.catalogue_id = String(data.get("catalogue_id") ?? ""); record.params.item_id = String(data.get("item_id") ?? ""); }
    else record.routine = String(data.get("routine") ?? "");
    this.editing = { intentId: String(data.get("intent_id") ?? ""), record };
  }
  async reconcileAfterAmbiguousFailure(message) { this.status = await this.adapter.status().catch(() => null); await this.loadRecords(this.status?.draft_state === "valid" ? "draft" : "active", false); this.notice = { kind: "warning", text: message }; }
  async saveEditor() {
    if (!this.canEditCurrentView()) return;
    const form = this.shadowRoot.querySelector("form"); this.updateEditorFromForm(form); this.editorErrors = validateIntentEntry(this.editing);
    if (Object.keys(this.editorErrors).length) { this.render(); return; }
    this.busy = true; this.render();
    try {
      await this.adapter.requireCapability("validation.record");
      const validation = await this.adapter.call("validateRecord", { intent_id: this.editing.intentId, record: this.editing.record });
      if (!validation.ok) { this.notice = { kind: "error", text: errorText(validation, "The provider rejected this record.") }; return; }
      const result = await this.adapter.guardedMutation(this.original.intentId ? "update" : "create", { intent_id: this.editing.intentId, record: this.editing.record });
      if (result.conflict) { this.status = result.refreshed_status; this.records = (result.refreshed_view?.records ?? []).map(({ intent_id: id, record }) => normalizeIntentEntry(id, record)); this.notice = { kind: "warning", text: "The shared draft changed elsewhere. The latest draft was loaded; your edit was not retried or overwritten." }; return; }
      if (!result.ok) { this.notice = { kind: "error", text: errorText(result, "Save failed.") }; return; }
      this.status = await this.adapter.status(); await this.loadRecords("draft", false); this.screen = "list"; this.editing = null; this.original = null; this.notice = { kind: "success", text: "Saved to the shared draft. Active runtime state is unchanged." };
    } catch (error) {
      if (error.kind === "timeout") await this.reconcileAfterAmbiguousFailure("The save timed out, so its outcome is uncertain. Current provider state was reloaded; review it before trying again.");
      else this.notice = { kind: "error", text: `${error.code ?? "error"}: ${error.message}` };
    } finally { this.busy = false; this.render(); }
  }
  async deleteEditor() {
    if (!this.canEditCurrentView()) return;
    if (!this.original?.intentId || !globalThis.confirm?.(`Stage deletion of ${this.original.intentId}?`)) return;
    this.busy = true; this.render();
    try {
      const result = await this.adapter.guardedMutation("delete", { intent_id: this.original.intentId });
      if (result.conflict) { this.status = result.refreshed_status; this.records = (result.refreshed_view?.records ?? []).map(({ intent_id: id, record }) => normalizeIntentEntry(id, record)); this.notice = { kind: "warning", text: "The shared draft changed elsewhere. Nothing was deleted; the latest draft was loaded." }; return; }
      if (!result.ok) { this.notice = { kind: "error", text: errorText(result, "Delete failed.") }; return; }
      this.status = await this.adapter.status(); await this.loadRecords("draft", false); this.screen = "list"; this.editing = null; this.original = null; this.notice = { kind: "success", text: "Deletion staged in the shared draft. Active runtime state is unchanged." };
    } catch (error) {
      if (error.kind === "timeout") await this.reconcileAfterAmbiguousFailure("The delete timed out, so its outcome is uncertain. Current provider state was reloaded; review it before trying again.");
      else this.notice = { kind: "error", text: `${error.code ?? "error"}: ${error.message}` };
    } finally { this.busy = false; this.render(); }
  }

  bindRowEvents() {
    const root = this.shadowRoot;
    root.querySelectorAll("[data-intent-id]").forEach((row) => {
      const open = () => this.openEditor(this.records.find((entry) => entry.intentId === row.dataset.intentId)); row.addEventListener("click", open);
      row.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") open(); });
    });
  }
  bindListEvents() {
    const root = this.shadowRoot;
    root.querySelector("[data-action=add]")?.addEventListener("click", () => this.openEditor());
    this.bindRowEvents();
    for (const field of ["search", "type", "sort"]) root.querySelector(`[name=${field}]`)?.addEventListener(field === "search" ? "input" : "change", (event) => {
      this.filters[field] = event.target.value;
      this.listScrollTop = field === "search" ? 0 : root.querySelector(".table-wrap")?.scrollTop ?? 0;
      this.updateListResults();
    });
    root.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => { if (button.dataset.view !== this.view && !this.busy) void this.loadRecords(button.dataset.view); }));
    const wrap = root.querySelector(".table-wrap"); if (wrap) wrap.scrollTop = this.listScrollTop;
  }
  bindEditorEvents() {
    const root = this.shadowRoot; const form = root.querySelector("form");
    root.querySelector("[data-action=cancel]")?.addEventListener("click", () => this.closeEditor());
    root.querySelector("[data-action=delete]")?.addEventListener("click", () => void this.deleteEditor());
    form?.addEventListener("submit", (event) => { event.preventDefault(); void this.saveEditor(); });
    form?.addEventListener("input", () => this.updateEditorFromForm(form));
    form?.querySelector("[name=intent]")?.addEventListener("change", () => { this.updateEditorFromForm(form); this.editing.record = { ...blankIntentRecord(this.editing.record.intent), title: this.editing.record.title, ...(this.editing.record.area_override ? { area_override: this.editing.record.area_override } : {}) }; this.render(); });
  }
  renderNotice() { return this.notice ? `<div class="notice ${escapeHtml(this.notice.kind)}" role="status">${escapeHtml(this.notice.text)}</div>` : ""; }
  visibleRecords() { return filterAndSortIntents(this.records, this.filters); }
  renderIntentRows(visible = this.visibleRecords()) {
    return visible.map(({ intentId, record }) => {
      const count = this.tagCounts.has(intentId) ? this.tagCounts.get(intentId) : undefined; const tags = count === undefined ? "…" : count === null ? "Unavailable" : String(count);
      return `<div class="intent-row" role="row" tabindex="0" data-intent-id="${escapeHtml(intentId)}"><div role="cell"><strong>${escapeHtml(record.title)}</strong><small>${escapeHtml(intentId)}</small></div><div role="cell"><span class="type">${escapeHtml(record.intent)}</span></div><div role="cell" class="tags" aria-label="${escapeHtml(tags)} associated tags">${escapeHtml(tags)}</div><div class="chevron">›</div></div>`;
    }).join("") || `<p class="empty">No intents match the current search and filter.</p>`;
  }
  updateListResults() {
    if (this.screen !== "list" || !this.shadowRoot) return;
    const visible = this.visibleRecords(); const table = this.shadowRoot.querySelector(".intent-table");
    const resultCount = this.shadowRoot.querySelector(".result-count"); const wrap = this.shadowRoot.querySelector(".table-wrap");
    if (resultCount) resultCount.textContent = `${visible.length} of ${this.records.length} intents`;
    if (table) {
      table.innerHTML = `<div class="intent-head" role="row"><div>Name / ID</div><div>Type</div><div>Tags</div><div></div></div>${this.renderIntentRows(visible)}`;
      this.bindRowEvents();
    }
    if (wrap) wrap.scrollTop = this.listScrollTop;
  }
  renderList() {
    const visible = this.visibleRecords(); const canDraft = this.adapter.capabilities?.capabilities?.includes("draft.list"); const draftAvailable = this.status?.draft_state === "valid";
    const rows = this.renderIntentRows(visible);
    return `<main><header><div><h1>Intent Catalogue</h1><p class="permission">${this.adapter.canManage ? "Administrator · edits are staged" : "Read only"}</p></div>${this.canEditCurrentView() ? `<button class="primary" data-action="add">Add intent</button>` : ""}</header>${this.renderNotice()}
      <section class="state-bar"><div class="view-switch"><button data-view="active" class="${this.view === "active" ? "selected" : ""}">Active</button><button data-view="draft" class="${this.view === "draft" ? "selected" : ""}" ${!canDraft || !draftAvailable ? "disabled" : ""}>Shared draft</button></div><span>${this.view === "draft" ? "Viewing staged changes; runtime remains active." : draftAvailable ? "A shared draft exists." : "No staged draft."}</span></section>
      <section class="toolbar"><label class="search"><span>Search</span><input name="search" type="search" value="${escapeHtml(this.filters.search)}" placeholder="ID or Name"></label><label><span>Type</span><select name="type"><option value="all" ${this.filters.type === "all" ? "selected" : ""}>All types</option><option value="media.play_source" ${this.filters.type === "media.play_source" ? "selected" : ""}>Play source</option><option value="routine.run" ${this.filters.type === "routine.run" ? "selected" : ""}>Run routine</option></select></label><label><span>Sort</span><select name="sort"><option value="id-asc" ${this.filters.sort === "id-asc" ? "selected" : ""}>ID A–Z</option><option value="id-desc" ${this.filters.sort === "id-desc" ? "selected" : ""}>ID Z–A</option><option value="name-asc" ${this.filters.sort === "name-asc" ? "selected" : ""}>Name A–Z</option><option value="name-desc" ${this.filters.sort === "name-desc" ? "selected" : ""}>Name Z–A</option></select></label></section>
      <div class="result-count">${visible.length} of ${this.records.length} intents</div><section class="table-wrap" aria-busy="${this.busy}"><div class="intent-table" role="table"><div class="intent-head" role="row"><div>Name / ID</div><div>Type</div><div>Tags</div><div></div></div>${rows}</div></section></main>`;
  }
  field(name, label, value, { readonly = false, required = true, hint = "" } = {}) {
    const error = this.editorErrors[name]; const readOnly = readonly || !this.canEditCurrentView();
    return `<label class="field"><span>${escapeHtml(label)}${required ? " *" : ""}</span><input name="${escapeHtml(name)}" value="${escapeHtml(value)}" ${readOnly ? "readonly" : ""} ${required ? "required" : ""} aria-invalid="${error ? "true" : "false"}">${hint ? `<small>${escapeHtml(hint)}</small>` : ""}${error ? `<small class="field-error">${escapeHtml(error)}</small>` : ""}</label>`;
  }
  renderEditor() {
    const existing = Boolean(this.original?.intentId); const record = this.editing.record; const editable = this.canEditCurrentView(); const disabled = !editable || this.busy;
    const typeFields = record.intent === "routine.run" ? this.field("routine", "Routine ID", record.routine ?? "") : `${this.field("output_domain", "Output domain", record.params?.output?.domain ?? "")}${this.field("catalogue_id", "Catalogue ID", record.params?.catalogue_id ?? "")}${this.field("item_id", "Item ID", record.params?.item_id ?? "")}`;
    return `<main class="editor"><header><div><button class="back" type="button" data-action="cancel">‹</button><h1>${existing ? escapeHtml(record.title || this.editing.intentId) : "Add intent"}</h1><p class="permission">General · ${editable ? "Save stages changes only" : this.adapter.canManage ? "Active comparison is read only while a shared draft exists" : "Read only"}</p></div></header>${this.renderNotice()}<form>
      <section class="card"><h2>General</h2><div class="form-grid">${this.field("intent_id", "Intent ID", this.editing.intentId, { readonly: existing, hint: existing ? "Intent ID cannot be changed after creation." : "Lower-case letters, numbers and underscores." })}${this.field("title", "Name", record.title ?? "")}
      <label class="field"><span>Intent type *</span><select name="intent" ${!editable ? "disabled" : ""}><option value="media.play_source" ${record.intent === "media.play_source" ? "selected" : ""}>Play media source</option><option value="routine.run" ${record.intent === "routine.run" ? "selected" : ""}>Run routine</option></select>${!editable ? `<input type="hidden" name="intent" value="${escapeHtml(record.intent)}">` : ""}</label>${this.field("area_override", "Area override", record.area_override ?? "", { required: false, hint: "Optional canonical Home Assistant area ID." })}</div></section>
      <section class="card"><h2>${record.intent === "routine.run" ? "Routine" : "Media source"}</h2><div class="form-grid">${typeFields}</div></section>
      <div class="editor-actions">${existing && editable ? `<button type="button" class="danger" data-action="delete" ${disabled ? "disabled" : ""}>Delete</button>` : ""}<span></span><button type="button" data-action="cancel">Cancel</button>${editable ? `<button type="submit" class="primary" ${disabled ? "disabled" : ""}>${this.busy ? "Saving…" : "Save"}</button>` : ""}</div></form></main>`;
  }
  render() {
    if (!this.shadowRoot || !this._hass) return;
    this.shadowRoot.innerHTML = `<style>
      :host{display:block;min-height:100%;color:var(--primary-text-color);background:var(--primary-background-color);font-family:sans-serif}*{box-sizing:border-box}main{width:min(72rem,100%);min-height:100%;margin:auto;padding:max(1rem,env(safe-area-inset-top)) max(1rem,env(safe-area-inset-right)) max(1rem,env(safe-area-inset-bottom)) max(1rem,env(safe-area-inset-left))}header{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-bottom:1rem}h1{margin:0;font-size:clamp(1.45rem,4vw,2rem)}h2{margin:0 0 1rem;font-size:1.15rem}.permission,small,.result-count{color:var(--secondary-text-color)}.permission{margin:.25rem 0 0}button,input,select{min-height:2.75rem;border:1px solid var(--divider-color);border-radius:.5rem;padding:.55rem .75rem;color:var(--primary-text-color);background:var(--card-background-color);font:inherit}button{cursor:pointer}button:disabled{opacity:.5;cursor:not-allowed}button.primary{border-color:var(--primary-color);color:var(--text-primary-color,#fff);background:var(--primary-color)}button.danger{color:var(--error-color);border-color:var(--error-color);background:transparent}.notice{margin:.75rem 0;padding:.75rem 1rem;border-radius:.5rem;background:var(--card-background-color);border-inline-start:.3rem solid var(--primary-color)}.notice.error{border-color:var(--error-color)}.notice.success{border-color:var(--success-color,#2e7d32)}.notice.warning{border-color:var(--warning-color,#ed8b00)}
      .state-bar{display:flex;align-items:center;gap:1rem;justify-content:space-between;padding:.65rem;margin-bottom:.75rem;border-radius:.6rem;background:var(--card-background-color)}.view-switch{display:flex}.view-switch button{border-radius:0;min-height:2.25rem;padding:.35rem .7rem}.view-switch button:first-child{border-radius:.4rem 0 0 .4rem}.view-switch button:last-child{border-radius:0 .4rem .4rem 0}.view-switch .selected{color:var(--text-primary-color,#fff);background:var(--primary-color);border-color:var(--primary-color)}.toolbar{display:grid;grid-template-columns:minmax(14rem,2fr) minmax(9rem,1fr) minmax(9rem,1fr);gap:.75rem;margin:.75rem 0}label>span{display:block;margin-bottom:.3rem;font-size:.82rem;font-weight:600}input,select{width:100%}.result-count{margin:.5rem 0;font-size:.85rem}.table-wrap{max-height:calc(100vh - 20rem);overflow:auto;border-radius:.65rem;background:var(--card-background-color);box-shadow:var(--ha-card-box-shadow,none)}.intent-head,.intent-row{display:grid;grid-template-columns:minmax(12rem,2fr) minmax(9rem,1fr) 5rem 1.5rem;align-items:center;gap:.75rem;padding:.7rem 1rem}.intent-head{position:sticky;top:0;z-index:1;color:var(--secondary-text-color);background:var(--card-background-color);border-bottom:1px solid var(--divider-color);font-size:.78rem;font-weight:700;text-transform:uppercase}.intent-row{border-bottom:1px solid var(--divider-color);cursor:pointer}.intent-row:hover,.intent-row:focus{outline:none;background:var(--secondary-background-color)}.intent-row strong,.intent-row small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.type{display:inline-block;padding:.2rem .45rem;border-radius:1rem;background:var(--secondary-background-color);font-size:.78rem}.tags{text-align:center}.chevron{font-size:1.5rem;color:var(--secondary-text-color)}.empty{padding:2rem;text-align:center;color:var(--secondary-text-color)}
      .editor{max-width:52rem}.editor header>div{display:grid;grid-template-columns:auto 1fr;column-gap:.75rem;align-items:center}.editor header .permission{grid-column:2}.back{grid-row:1/span 2;border:0;background:transparent;font-size:2rem;padding:.25rem}.card{margin:0 0 1rem;padding:1rem;border-radius:.65rem;background:var(--card-background-color);box-shadow:var(--ha-card-box-shadow,none)}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.field small{display:block;margin-top:.25rem}.field-error{color:var(--error-color)}[aria-invalid=true]{border-color:var(--error-color)}.editor-actions{position:sticky;bottom:0;display:grid;grid-template-columns:auto 1fr auto auto;gap:.75rem;padding:max(.75rem,env(safe-area-inset-bottom)) 0;background:var(--primary-background-color)}.loading{display:grid;min-height:15rem;place-items:center;color:var(--secondary-text-color)}
      @media(max-width:640px){main{padding-inline:max(.75rem,env(safe-area-inset-left))}.state-bar{align-items:flex-start;flex-direction:column;gap:.5rem}.toolbar{grid-template-columns:1fr 1fr}.toolbar .search{grid-column:1/-1}.table-wrap{max-height:none;overflow:visible;background:transparent;box-shadow:none}.intent-head{display:none}.intent-row{grid-template-columns:1fr auto 1.25rem;margin-bottom:.55rem;border:0;border-radius:.6rem;background:var(--card-background-color);box-shadow:var(--ha-card-box-shadow,none)}.intent-row [role=cell]:nth-child(2){grid-column:1}.intent-row .tags{grid-column:2;grid-row:1/span 2}.intent-row .chevron{grid-column:3;grid-row:1/span 2}.intent-row .tags::after{content:" tags";font-size:.75rem;color:var(--secondary-text-color)}.form-grid{grid-template-columns:1fr}.editor-actions{grid-template-columns:1fr 1fr}.editor-actions span{display:none}.editor-actions .danger{grid-column:1/-1;order:3}}
    </style>${this.busy && !this.initialized ? `<main><div class="loading">Loading Intent Catalogue…</div>${this.renderNotice()}</main>` : this.screen === "editor" ? this.renderEditor() : this.renderList()}`;
    if (this.screen === "editor") this.bindEditorEvents(); else this.bindListEvents();
  }
}

if (globalThis.customElements && !globalThis.customElements.get("astv-intent-catalogue-panel")) globalThis.customElements.define("astv-intent-catalogue-panel", ASTVIntentCataloguePanel);
