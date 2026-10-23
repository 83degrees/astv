import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import {
  classifyAuthenticationState,
  permissionProbeRequest,
  requireBackendUnauthorizedProof,
} from "../06_Validation/Staging/ASTV-353/browser/browser-contract.mjs";

const workflow = fs.readFileSync(".github/workflows/astv-353-disposable-staging.yml", "utf8");
const catalogue = fs.readFileSync("06_Validation/Staging/ASTV-353/config/astv/astv_intent_catalogue.yaml", "utf8");
const mapping = fs.readFileSync("06_Validation/Staging/ASTV-353/config/AdvNFC/advnfc_tag_mapping.yaml", "utf8");
const browser = fs.readFileSync("06_Validation/Staging/ASTV-353/browser/browser.spec.mjs", "utf8");
const playwrightConfig = fs.readFileSync("06_Validation/Staging/ASTV-353/browser/playwright.config.mjs", "utf8");
const lifecycle = fs.readFileSync("06_Validation/Staging/ASTV-353/config/staging/lifecycle.py", "utf8");
const restorationVerifier = fs.readFileSync("06_Validation/Staging/ASTV-353/config/staging/verify_restoration.py", "utf8");
const prepareStage = fs.readFileSync("06_Validation/Staging/ASTV-353/config/staging/prepare_stage.py", "utf8");
const sanitizer = "06_Validation/Staging/ASTV-353/config/staging/sanitize_evidence.py";
const evidenceControls = "06_Validation/Staging/ASTV-353/config/staging/evidence_controls.py";
const evidenceControlsSource = fs.readFileSync(evidenceControls, "utf8");
const permissionVerifier = "06_Validation/Staging/ASTV-353/config/staging/verify_permission_evidence.py";

const sha256 = (path) => crypto.createHash("sha256").update(fs.readFileSync(path)).digest("hex");
const pythonCommand = () => process.env.ASTV353_PYTHON || (process.platform === "win32" ? "py" : "python3");
const runPython = (script, args) => spawnSync(pythonCommand(), [script, ...args], { encoding: "utf8" });

function createPreparedStage(root, mode = "read_only") {
  const evidence = path.join(root, "evidence");
  const config = path.join(root, "config");
  const catalogue = path.join(config, "astv", "astv_intent_catalogue.yaml");
  const mapping = path.join(config, "AdvNFC", "advnfc_tag_mapping.yaml");
  fs.mkdirSync(path.dirname(catalogue), { recursive: true });
  fs.mkdirSync(path.dirname(mapping), { recursive: true });
  fs.mkdirSync(path.join(config, "staging"), { recursive: true });
  fs.mkdirSync(evidence, { recursive: true });
  fs.writeFileSync(catalogue, "schema: astv.intent_catalogue\nrecords: {}\n");
  fs.writeFileSync(mapping, "mappings: {}\n");
  fs.writeFileSync(path.join(config, "configuration.yaml"), "default_config:\n");
  fs.writeFileSync(path.join(config, "staging", "prepare_stage.py"), "pass\n");
  fs.writeFileSync(path.join(config, "staging", "browser-session.json"), "{}\n");
  fs.writeFileSync(path.join(config, "staging", "private-artifact-secrets.json"), "{}\n");
  fs.writeFileSync(path.join(evidence, "stage-prepared.status"), "prepared\n");
  fs.writeFileSync(path.join(evidence, "browser-execution.status"), "passed\n");
  fs.writeFileSync(path.join(evidence, "workflow-invocation.json"), JSON.stringify({ mode }));
  fs.writeFileSync(
    path.join(evidence, "config-before.sha256"),
    `${sha256(catalogue)}  ${catalogue.replaceAll("\\", "/")}\n${sha256(mapping)}  ${mapping.replaceAll("\\", "/")}\n`,
  );
  return { catalogue, config, evidence, mapping };
}

test("workflow exposes distinct exact-PR Stage 2 and Stage 3 label routes and always disposes resources", () => {
  assert.match(workflow, /pull_request:/);
  assert.match(workflow, /types:\s*\n\s*- labeled/);
  assert.doesNotMatch(workflow, /workflow_dispatch:/);
  assert.doesNotMatch(workflow, /pull_request_target:/);
  assert.doesNotMatch(workflow, /\n\s+(push|schedule):/);
  assert.match(workflow, /github\.event_name == 'pull_request'/);
  assert.match(workflow, /github\.event\.action == 'labeled'/);
  assert.match(workflow, /github\.event\.label\.name == 'ASTV-353-STEP2-READ-ONLY'/);
  assert.match(workflow, /github\.event\.label\.name == 'ASTV-353-STAGE3-CONTROLLED-LIFECYCLE'/);
  assert.match(workflow, /github\.event\.pull_request\.number == 130/);
  assert.match(workflow, /github\.event\.pull_request\.base\.ref == 'beta'/);
  assert.match(workflow, /github\.event\.pull_request\.head\.ref == 'gsheldon\/astv-353-stage2-step1-offline-preparation'/);
  assert.match(workflow, /github\.event\.pull_request\.head\.repo\.full_name == github\.repository/);
  assert.match(workflow, /EFFECTIVE_MODE: \$\{\{ github\.event\.label\.name == 'ASTV-353-STAGE3-CONTROLLED-LIFECYCLE'/);
  assert.match(workflow, /EXPECTED_HEAD_SHA: \$\{\{ github\.event\.pull_request\.head\.sha \}\}/);
  assert.match(workflow, /ASTV-353-STEP2-READ-ONLY\)\s*\n\s*test "\$\{EFFECTIVE_MODE\}" = "read_only"/);
  assert.match(workflow, /ASTV-353-STAGE3-CONTROLLED-LIFECYCLE\)\s*\n\s*test "\$\{EFFECTIVE_MODE\}" = "controlled_lifecycle"/);
  assert.doesNotMatch(workflow, /\$\{\{\s*secrets\./);
  assert.match(workflow, /permissions:\s*\n\s+contents: read/);
  assert.match(workflow, /docker network create --internal/);
  assert.doesNotMatch(workflow, /^\s+(--publish|-p\s)/m);
  assert.match(workflow, /if: always\(\)/);
  assert.match(workflow, /docker rm --force/);
  assert.match(workflow, /docker network rm/);
  assert.match(workflow, /cleanup_rc=1/);
  assert.match(workflow, /containers_removed=false/);
  assert.match(workflow, /test "\$\{permission_rc\}" -eq 0 && test "\$\{privacy_rc\}" -eq 0 && test "\$\{cleanup_rc\}" -eq 0/);
});
test("accepted product and platform identities are explicit and fail closed", () => {
  assert.match(workflow, /v0\.5\.0-beta\.c630ce5/);
  assert.match(workflow, /c630ce5c1ba57cdb4d69b9185adc4a3eed60f7cd/);
  assert.match(workflow, /v1\.6\.0-beta\.dbef2f5/);
  assert.match(workflow, /dbef2f5133d2efb6f426b348916dc0c58ec1e147/);
  assert.match(workflow, /home-assistant:2026\.9\.4/);
  assert.match(workflow, /playwright:v1\.56\.1-noble/);
  assert.match(workflow, /sha256sum/);
  assert.match(workflow, /RepoDigests/);
});

test("runtime ownership is derived from the pinned HA image and never made group/world writable", () => {
  const ownership = workflow.indexOf("Prepare owner-only writable Home Assistant configuration");
  const startup = workflow.indexOf("Start internal-only Home Assistant stage");
  assert.ok(ownership > 0 && ownership < startup);
  assert.match(workflow, /os\.getuid\(\).*os\.getgid\(\)/);
  assert.match(workflow, /chown -R "\$\{ha_uid\}:\$\{ha_gid\}"/);
  assert.match(workflow, /find "\$\{config_root\}" -perm \/022/);
  assert.match(workflow, /\/config\/deps/);
  assert.match(workflow, /browser-runtime-identity\.json/);
  assert.match(workflow, /browser-evidence:\/evidence:rw/);
  assert.match(workflow, /browser-evidence\/\." "\$\{stage_root\}\/evidence\//);
  assert.doesNotMatch(workflow, /chmod\s+(?:-R\s+)?0?777/);
  assert.doesNotMatch(workflow, /--privileged/);
});

test("no-published-ports assertion accepts only explicit null or an empty object", () => {
  const jqAssertion = 'has("published_ports") and ((.published_ports | type) == "null" or ((.published_ports | type) == "object" and (.published_ports | length) == 0))';
  assert.ok(workflow.includes(`jq -e '${jqAssertion}'`));

  const acceptsNoPublishedPorts = (isolation) => {
    if (!Object.hasOwn(isolation, "published_ports")) return false;
    const bindings = isolation.published_ports;
    return bindings === null || (
      typeof bindings === "object" &&
      !Array.isArray(bindings) &&
      Object.keys(bindings).length === 0
    );
  };

  assert.equal(acceptsNoPublishedPorts({ published_ports: null }), true);
  assert.equal(acceptsNoPublishedPorts({ published_ports: {} }), true);
  assert.equal(acceptsNoPublishedPorts({ published_ports: { "8123/tcp": [{ HostPort: "8123" }] } }), false);
  for (const invalid of [[], "", 0, false]) {
    assert.equal(acceptsNoPublishedPorts({ published_ports: invalid }), false);
  }
  assert.equal(acceptsNoPublishedPorts({}), false);
});

test("bootstrap completes HA onboarding before config-entry and browser preparation", () => {
  for (const endpoint of ["core_config", "analytics", "integration"]) {
    assert.match(prepareStage, new RegExp(`/api/onboarding/${endpoint}`));
  }
  assert.match(prepareStage, /all\(step\.get\("done"\) is True for step in steps\)/);
  assert.ok(prepareStage.indexOf("onboarding = complete_onboarding(owner_token)") < prepareStage.indexOf("asyncio.run(prepare"));
});

test("config-entry bootstrap uses the authenticated Home Assistant REST flow", () => {
  assert.match(prepareStage, /post_json\(\s*"\/api\/config\/config_entries\/flow"/);
  assert.match(prepareStage, /post_json\(f"\/api\/config\/config_entries\/flow\/\{flow_id\}", \{\}, token\)/);
  assert.match(prepareStage, /"Authorization"\] = f"Bearer \{token\}"/);
  assert.match(prepareStage, /"handler": "astv_intent_catalogue"/);
  assert.match(prepareStage, /configured\.get\("type"\) == "create_entry"/);
  assert.doesNotMatch(prepareStage, /config_entries\/flow\/(init|configure)/);
});

test("fixtures are synthetic, inert, and preserve the read-only product boundary", () => {
  assert.deepEqual([...catalogue.matchAll(/^  (astv353_[a-z_]+):$/gm)].map((match) => match[1]), [
    "astv353_referenced", "astv353_validation", "astv353_missing_media",
  ]);
  assert.match(mapping, /A3530001/);
  assert.match(mapping, /intent_id: astv353_referenced/);
  for (const forbidden of ["ha-starburst", "assistive/nfc", "mqtt:", "DEADBEEF"]) {
    assert.equal(catalogue.includes(forbidden) || mapping.includes(forbidden), false);
  }
  assert.equal(sha256("06_Validation/Staging/ASTV-353/config/astv/astv_intent_catalogue.yaml"), "b00da33486bad0d68673b84d765f0115f14ecd719815fe2bb00f741555f7d7f2");
  assert.equal(sha256("06_Validation/Staging/ASTV-353/config/AdvNFC/advnfc_tag_mapping.yaml"), "79376c93e86e676b062628aa81c618d6c92ad4f7d6af9aba1a635bda592daa7d");
  assert.equal(sha256("06_Validation/Staging/ASTV-353/config/custom_components/mediacat/__init__.py"), "8c2c15931d21556d3381b23697227daf4e3ae0875addcf079407becb05fd1910");
});

test("offline contracts cover startup, authentication, selectors, permissions, isolation, and teardown", () => {
  assert.match(workflow, /"\$\{HA_IMAGE\}" -m homeassistant --config \/config/);
  assert.match(workflow, /docker exec "\$\{STAGE_CONTAINER\}" python3 \/config\/staging\/prepare_stage\.py/);
  assert.match(prepareStage, /\/api\/onboarding\/users/);
  assert.match(prepareStage, /\/auth\/token/);
  assert.match(prepareStage, /type="config\/auth\/create"/);
  assert.match(prepareStage, /group_ids=\["system-users"\]/);
  assert.match(browser, /input\[name="username"\]/);
  assert.match(browser, /input\[name="password"\]/);
  assert.match(browser, /getByRole\("button", \{ name: \/log in\/i \}\)/);
  assert.match(browser, /getByRole\("heading", \{ name: "Intent Catalogue", level: 1 \}\)/);
  assert.match(browser, /getByRole\("button", \{ name: "Add intent" \}\)/);
  assert.match(workflow, /docker network create --internal/);
  assert.match(workflow, /--cap-drop ALL/);
  assert.match(workflow, /--security-opt no-new-privileges/);
  assert.match(workflow, /if: always\(\)/);
  assert.match(workflow, /containers_removed=true/);
  assert.match(workflow, /network_removed=true/);
});

test("ordinary PR updates cannot start the stage and the labeled route checks out the immutable PR head", () => {
  assert.doesNotMatch(workflow, /synchronize|opened|reopened/);
  assert.match(workflow, /ref: \$\{\{ github\.event\.pull_request\.head\.sha \}\}/);
  assert.match(workflow, /test "\$\(git rev-parse HEAD\)" = "\$\{EXPECTED_HEAD_SHA\}"/);
  assert.match(workflow, /PR_ACTION: \$\{\{ github\.event\.action \}\}/);
  assert.match(workflow, /test "\$\{PR_ACTION\}" = "labeled"/);
  assert.doesNotMatch(workflow, /synchronize|opened|reopened|workflow_dispatch|pull_request_target/);
  assert.match(workflow, /case "\$\{PR_LABEL\}" in/);
  assert.match(workflow, /\*\)\s*\n\s*exit 1/);
});

test("Playwright resolves the copied test beside its offline-installed packages", () => {
  const install = workflow.indexOf("npm install --offline");
  const copy = workflow.indexOf("cp /work/*.mjs .");
  const execute = workflow.indexOf("npx playwright test --config ./playwright.config.mjs ./browser.spec.mjs");
  assert.ok(install > 0 && install < copy && copy < execute);
  assert.match(playwrightConfig, /testDir: "\."/);
  assert.doesNotMatch(playwrightConfig, /testDir: "\/work"/);
  assert.doesNotMatch(workflow, /playwright test[^\n']*\/work\/browser\.spec\.mjs/);
});

test("browser and lifecycle suites cover the approved acceptance matrix", () => {
  for (const required of ["desktop", "mobile", "non-admin", "Add intent", "Save stages changes only", "A3530001"]) {
    assert.match(browser, new RegExp(required, "i"));
  }
  for (const required of ["create_save", "stale_revision", "validation_error", "mediacat_activation_error", "explicit_activate", "edit_save", "delete_save", "baseline_bytes_restored"]) {
    assert.match(lifecycle, new RegExp(required));
  }
  assert.match(browser, /known AdvNFC reference prevents deletion in the UI/);
  assert.match(workflow, /Run controlled synthetic lifecycle and prove restoration/);
  assert.match(workflow, /docker restart "\$\{STAGE_CONTAINER\}"/);
  assert.match(workflow, /verify_restoration\.py/);
  assert.match(lifecycle, /primary_failure/);
  assert.match(lifecycle, /DRAFT\.unlink\(missing_ok=True\)/);
  assert.match(restorationVerifier, /active_revision_mismatch/);
  assert.match(restorationVerifier, /active_fixture_mismatch/);
});

test("referenced-delete browser check requires the exact warning and proves no catalogue mutation", () => {
  const testStart = browser.indexOf('test("known AdvNFC reference prevents deletion in the UI"');
  const testBlock = browser.slice(testStart);
  assert.ok(testStart >= 0);
  assert.match(testBlock, /Deletion is blocked because AdvNFC references this intent: ASTV 353 synthetic reference \(A3530001\)\. Manage those provider-owned mappings in AdvNFC first\./);
  assert.match(testBlock, /expect\(blockingNotice\)\.toContainText\("A3530001"\)/);
  assert.doesNotMatch(testBlock, /referenced by AdvNFC/i);
  assert.match(testBlock, /const beforeDelete = await readCatalogueState\(page\)/);
  assert.match(testBlock, /expect\(beforeDelete\.draft_state\)\.toBe\("absent"\)/);
  assert.match(testBlock, /expect\(beforeDelete\.intent_ids\)\.toContain\("astv353_referenced"\)/);
  assert.match(testBlock, /const afterDelete = await readCatalogueState\(page\)/);
  assert.match(testBlock, /expect\(afterDelete\)\.toEqual\(beforeDelete\)/);
  assert.match(testBlock, /getByRole\("heading", \{ name: "ASTV 353 referenced routine", level: 1 \}\)/);
  assert.doesNotMatch(testBlock, /create_intent_record|update_intent_record|delete_intent_record|activate_intent_catalogue/);
  assert.match(browser, /service,\s*service_data: serviceData/);
  assert.match(browser, /call\("get_administration_status"\)/);
  assert.match(browser, /call\("list_intent_records", \{ view: "active", limit: 200 \}\)/);
});

test("login waits for authenticated HA state and explicitly routes to the panel", () => {
  assert.equal(classifyAuthenticationState({ authenticated: false, error: null }), "pending");
  assert.equal(classifyAuthenticationState({ authenticated: false, error: "Invalid authentication" }), "authentication_error");
  assert.equal(classifyAuthenticationState({ authenticated: true, error: null }), "authenticated");
  assert.doesNotMatch(browser, /waitForURL\(\/\\\/lovelace/);
  assert.match(browser, /Home Assistant authentication failed/);
  assert.match(browser, /PANEL_PATH/);
  assert.match(browser, /toHaveURL\(\/\\\/astv-intent-catalogue/);
  assert.match(browser, /typeof homeAssistant\.hass\.callWS === "function"/);
});

test("permission probe accepts only native Unauthorized or the audited HA wrapper", () => {
  assert.deepEqual(requireBackendUnauthorizedProof({ kind: "backend_denial", code: "unauthorized" }), {
    status: "passed", proof: "native_error_code",
  });
  assert.deepEqual(requireBackendUnauthorizedProof({ kind: "backend_denial", code: "home_assistant_error" }), {
    status: "pending_backend_log", proof: "exact_service_unauthorized_log",
  });
  for (const result of [
    { kind: "precondition_failure", reason: "missing_hass" },
    { kind: "precondition_failure", reason: "missing_callWS" },
    { kind: "unexpected_success" },
    { kind: "unexpected_exception", reason: "string" },
    { kind: "backend_denial", code: "invalid_format" },
    { kind: "backend_denial", code: "connection_error" },
  ]) assert.throws(() => requireBackendUnauthorizedProof(result));
  assert.deepEqual(permissionProbeRequest(), {
    type: "call_service",
    domain: "astv_intent_catalogue",
    service: "validate_intent_record",
    service_data: {
      intent_id: "astv353_validation",
      record: {
        intent: "media.play_source",
        title: "ASTV 353 validation media",
        params: {
          output: { domain: "audio" },
          catalogue_id: "astv_353_stage",
          item_id: "validation_media",
        },
      },
    },
    return_response: true,
  });
  assert.doesNotMatch(browser, /create_intent_record/);
  assert.match(browser, /status: verification\.status/);
  assert.match(workflow, /verify_permission_evidence\.py/);
  assert.match(workflow, /test "\$\{permission_rc\}" -eq 0/);
});

test("wrapped Home Assistant errors require the exact backend Unauthorized event", () => {
  const exactEvent = "Error during service call to astv_intent_catalogue.validate_intent_record: Unauthorized";
  const cases = [
    ["exact", exactEvent + "\n", 0],
    ["unrelated-service", "Error during service call to light.turn_on: Unauthorized\n", 1],
    ["different-exception", "Error during service call to astv_intent_catalogue.validate_intent_record: ValueError\n", 1],
    ["missing-log", null, 1],
  ];
  for (const [name, log, expectedStatus] of cases) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), `astv353-permission-${name}-`));
    try {
      fs.writeFileSync(path.join(root, "permission.json"), JSON.stringify({
        status: "pending_backend_log",
        proof: "exact_service_unauthorized_log",
        probe: { kind: "backend_denial", code: "home_assistant_error" },
      }));
      if (log !== null) fs.writeFileSync(path.join(root, "home-assistant.log"), log);
      const result = runPython(permissionVerifier, [root]);
      assert.equal(result.status, expectedStatus, `${name}: ${result.stderr}`);
      const report = JSON.parse(fs.readFileSync(path.join(root, "permission-proof.json"), "utf8"));
      assert.equal(report.status, expectedStatus === 0 ? "passed" : "failed");
    } finally {
      fs.rmSync(root, { recursive: true, force: true });
    }
  }
});

test("native structured Unauthorized is sufficient without diagnostic log parsing", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "astv353-native-permission-"));
  try {
    fs.writeFileSync(path.join(root, "permission.json"), JSON.stringify({
      status: "passed",
      proof: "native_error_code",
      probe: { kind: "backend_denial", code: "unauthorized" },
    }));
    const result = runPython(permissionVerifier, [root]);
    assert.equal(result.status, 0, result.stderr);
    const report = JSON.parse(fs.readFileSync(path.join(root, "permission-proof.json"), "utf8"));
    assert.equal(report.proof, "native_error_code");
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("read-only desktop coverage includes accessible focus and keyboard navigation", () => {
  assert.match(browser, /getByRole\("navigation", \{ name: "Intent Catalogue sections" \}\)/);
  assert.match(browser, /getByRole\("searchbox", \{ name: "Search" \}\)/);
  assert.match(browser, /getByRole\("combobox", \{ name: "Type" \}\)/);
  assert.match(browser, /getByRole\("combobox", \{ name: "Sort" \}\)/);
  assert.match(browser, /toBeFocused\(\)/);
  assert.match(browser, /keyboard\.press\("Tab"\)/);
  assert.match(browser, /keyboard\.press\("Enter"\)/);
});

test("failure-path evidence uses explicit states and teardown remains unconditional", () => {
  assert.match(workflow, /name: Capture fixture integrity and segregation evidence\s+if: always\(\)/);
  for (const state of ["not_run", "failed", "passed", "not_applicable_read_only"]) {
    assert.match(evidenceControlsSource, new RegExp(state));
  }
  assert.match(workflow, /stage-prepared\.status/);
  assert.match(workflow, /evidence_controls\.py" \\\n\s+post-browser/);
  assert.match(evidenceControlsSource, /post-browser-validation\.json/);
  assert.match(evidenceControlsSource, /fixture_integrity/);
  assert.match(evidenceControlsSource, /segregation/);
  assert.match(evidenceControlsSource, /lifecycle_validation/);
  assert.match(workflow, /docker rm --force/);
  assert.match(workflow, /docker network rm/);
});

test("Stage 3 evidence fails closed for mutation, restoration, and missing-evidence paths", () => {
  const validLifecycle = {
    outcome: "pass",
    baseline_bytes_restored: true,
    draft_removed: true,
    restoration: {
      status: "passed",
      catalogue_bytes_restored: true,
      draft_removed: true,
      active_revision_restored: true,
      active_fixture_restored: true,
    },
  };
  const cases = [
    ["passed", () => {}, 0],
    ["mutation-exception", (value) => { value.outcome = "failed"; value.primary_failure = { phase: "edit_save", type: "RuntimeError" }; }, 1],
    ["restoration-failure", (value) => { value.restoration.status = "failed"; value.restoration.active_revision_restored = false; }, 1],
    ["missing-evidence", null, 1],
  ];
  for (const [name, mutate, expectedStatus] of cases) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), `astv353-stage3-${name}-`));
    try {
      const { config, evidence } = createPreparedStage(root, "controlled_lifecycle");
      fs.writeFileSync(path.join(evidence, "lifecycle-execution.status"), "passed\n");
      if (mutate !== null) {
        const lifecycleEvidence = structuredClone(validLifecycle);
        mutate(lifecycleEvidence);
        fs.writeFileSync(path.join(config, "staging", "lifecycle-evidence.json"), JSON.stringify(lifecycleEvidence));
      }
      const result = runPython(evidenceControls, ["post-browser", root]);
      assert.equal(result.status, expectedStatus, `${name}: ${result.stderr}`);
      const report = JSON.parse(fs.readFileSync(path.join(evidence, "post-browser-validation.json"), "utf8"));
      assert.equal(report.lifecycle_validation, expectedStatus === 0 ? "passed" : "failed");
      assert.equal(report.restoration, expectedStatus === 0 ? "passed" : "failed");
    } finally {
      fs.rmSync(root, { recursive: true, force: true });
    }
  }
});

test("prepared-stage evidence fails closed for missing baseline, fixture, or configuration", () => {
  const completeRoot = fs.mkdtempSync(path.join(os.tmpdir(), "astv353-complete-"));
  try {
    const { evidence } = createPreparedStage(completeRoot);
    const complete = runPython(evidenceControls, ["post-browser", completeRoot]);
    assert.equal(complete.status, 0, complete.stderr);
    const report = JSON.parse(fs.readFileSync(path.join(evidence, "post-browser-validation.json"), "utf8"));
    assert.equal(report.fixture_integrity, "passed");
    assert.equal(report.segregation, "passed");
  } finally {
    fs.rmSync(completeRoot, { recursive: true, force: true });
  }

  const cases = [
    ["baseline", ({ evidence }) => fs.rmSync(path.join(evidence, "config-before.sha256"))],
    ["fixture", ({ catalogue }) => fs.rmSync(catalogue)],
    ["configuration", ({ config }) => fs.rmSync(path.join(config, "configuration.yaml"))],
  ];
  for (const [name, removeRequiredInput] of cases) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), `astv353-${name}-`));
    try {
      const paths = createPreparedStage(root);
      removeRequiredInput(paths);
      const result = runPython(evidenceControls, ["post-browser", root]);
      assert.notEqual(result.status, 0, `${name} unexpectedly passed: ${result.stderr}`);
      const report = JSON.parse(fs.readFileSync(path.join(paths.evidence, "post-browser-validation.json"), "utf8"));
      if (name === "configuration") assert.equal(report.segregation, "failed");
      else assert.equal(report.fixture_integrity, "failed");
      assert.equal(report.stage_preparation, "passed");
    } finally {
      fs.rmSync(root, { recursive: true, force: true });
    }
  }
});

test("privacy failure and residual private files deny artifact upload", () => {
  assert.match(workflow, /id: evidence_upload_gate/);
  assert.match(workflow, /if: always\(\) && steps\.evidence_upload_gate\.outputs\.safe == 'true'/);
  assert.doesNotMatch(workflow, /name: Upload immutable staging evidence\s+if: always\(\)\s+uses:/);

  const root = fs.mkdtempSync(path.join(os.tmpdir(), "astv353-upload-denied-"));
  try {
    const { config, evidence } = createPreparedStage(root);
    fs.writeFileSync(path.join(evidence, "unsafe-report.txt"), "synthetic-token remains");
    const sanitizerFailure = runPython(sanitizer, [path.join(root, "missing-secrets.json"), evidence]);
    assert.notEqual(sanitizerFailure.status, 0);
    fs.writeFileSync(path.join(evidence, "artifact-privacy.json"), '{"status":"failed"}\n');
    fs.writeFileSync(path.join(evidence, "post-browser-validation.json"), "{}\n");
    fs.writeFileSync(path.join(evidence, "disposal.txt"), "containers_removed=true\nnetwork_removed=true\n");
    assert.notEqual(runPython(evidenceControls, ["authorize-upload", root]).status, 0);

    fs.writeFileSync(path.join(evidence, "artifact-privacy.json"), JSON.stringify({
      status: "passed",
      trace_capture: "disabled",
      secret_patterns_checked: 5,
    }));
    assert.ok(fs.existsSync(path.join(config, "staging", "private-artifact-secrets.json")));
    assert.notEqual(runPython(evidenceControls, ["authorize-upload", root]).status, 0);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("browser secrets are minimized and artifact evidence is redacted", () => {
  assert.match(playwrightConfig, /trace: "off"/);
  assert.match(playwrightConfig, /screenshot: "off"/);
  assert.match(playwrightConfig, /video: "off"/);
  assert.match(workflow, /browser-session\.json:\/stage\/staging\/browser-session\.json:ro/);
  assert.doesNotMatch(workflow, /config:\/stage:ro/);
  assert.match(workflow, /chown "\$\{browser_uid\}:\$\{browser_gid\}" "\$\{stage_root\}\/config\/staging\/browser-session\.json"/);
  assert.match(workflow, /chmod 0400 "\$\{stage_root\}\/config\/staging\/browser-session\.json"/);
  assert.match(prepareStage, /browser_session\.chmod\(0o600\)/);
  assert.match(prepareStage, /private_secrets\.chmod\(0o600\)/);
  const browserSessionBlock = prepareStage.slice(
    prepareStage.indexOf("browser_session ="),
    prepareStage.indexOf("private_secrets ="),
  );
  assert.doesNotMatch(browserSessionBlock, /admin_access_token/);
  assert.match(workflow, /sanitize_evidence\.py/);
  assert.match(workflow, /private-artifact-secrets\.json/);

  const root = fs.mkdtempSync(path.join(os.tmpdir(), "astv353-privacy-"));
  try {
    const evidence = path.join(root, "evidence");
    fs.mkdirSync(evidence);
    const secrets = path.join(root, "secrets.json");
    fs.writeFileSync(secrets, JSON.stringify({
      admin: ["synthetic-admin", "synthetic-admin-password"],
      reader: ["synthetic-reader", "synthetic-reader-password"],
      admin_access_token: "synthetic-token",
    }));
    fs.writeFileSync(path.join(evidence, "diagnostic.txt"), "user=synthetic-admin token=synthetic-token useful-detail");
    fs.writeFileSync(path.join(evidence, "binary.bin"), Buffer.from("prefix synthetic-reader-password suffix"));
    const result = runPython(sanitizer, [secrets, evidence]);
    assert.equal(result.status, 0, result.stderr);
    assert.equal(fs.readFileSync(path.join(evidence, "diagnostic.txt"), "utf8"), "user=[REDACTED] token=[REDACTED] useful-detail");
    assert.equal(fs.readFileSync(path.join(evidence, "binary.bin"), "utf8"), "prefix [REDACTED] suffix");
    const privacy = JSON.parse(fs.readFileSync(path.join(evidence, "artifact-privacy.json"), "utf8"));
    assert.equal(privacy.status, "passed");
    assert.deepEqual(privacy.redacted_files, ["binary.bin", "diagnostic.txt"]);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
