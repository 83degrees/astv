import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const workflow = fs.readFileSync(".github/workflows/astv-353-disposable-staging.yml", "utf8");
const catalogue = fs.readFileSync("06_Validation/Staging/ASTV-353/config/astv/astv_intent_catalogue.yaml", "utf8");
const mapping = fs.readFileSync("06_Validation/Staging/ASTV-353/config/AdvNFC/advnfc_tag_mapping.yaml", "utf8");
const browser = fs.readFileSync("06_Validation/Staging/ASTV-353/browser/browser.spec.mjs", "utf8");
const lifecycle = fs.readFileSync("06_Validation/Staging/ASTV-353/config/staging/lifecycle.py", "utf8");
const prepareStage = fs.readFileSync("06_Validation/Staging/ASTV-353/config/staging/prepare_stage.py", "utf8");

test("workflow has a narrow read-only PR route, a human-gated manual route, and unconditional disposal", () => {
  assert.match(workflow, /workflow_dispatch:/);
  assert.match(workflow, /pull_request:/);
  assert.doesNotMatch(workflow, /pull_request_target:/);
  assert.doesNotMatch(workflow, /\n\s+(push|schedule):/);
  assert.match(workflow, /ASTV-353-G2/);
  assert.match(workflow, /github\.event\.pull_request\.number == 128/);
  assert.match(workflow, /github\.event\.pull_request\.base\.ref == 'beta'/);
  assert.match(workflow, /github\.event\.pull_request\.head\.repo\.full_name == github\.repository/);
  assert.match(workflow, /EFFECTIVE_MODE:.*'read_only'/);
  assert.match(workflow, /github\.event_name == 'workflow_dispatch' && inputs\.mode == 'controlled_lifecycle'/);
  assert.match(workflow, /docker network create --internal/);
  assert.doesNotMatch(workflow, /^\s+(--publish|-p\s)/m);
  assert.match(workflow, /if: always\(\)/);
  assert.match(workflow, /docker rm --force/);
  assert.match(workflow, /docker network rm/);
});
test("accepted product and platform identities are explicit and fail closed", () => {
  assert.match(workflow, /v0\.5\.0-beta\.603e6e1/);
  assert.match(workflow, /603e6e160b00a357c205b343a950ad64f5a1afae/);
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

test("fixtures are synthetic, inert, and preserve the read-only product boundary", () => {
  assert.deepEqual([...catalogue.matchAll(/^  (astv353_[a-z_]+):$/gm)].map((match) => match[1]), [
    "astv353_referenced", "astv353_validation", "astv353_missing_media",
  ]);
  assert.match(mapping, /A3530001/);
  assert.match(mapping, /intent_id: astv353_referenced/);
  for (const forbidden of ["ha-starburst", "assistive/nfc", "mqtt:", "DEADBEEF"]) {
    assert.equal(catalogue.includes(forbidden) || mapping.includes(forbidden), false);
  }
});

test("browser and lifecycle suites cover the approved acceptance matrix", () => {
  for (const required of ["desktop", "mobile", "non-admin", "Add intent", "Save stages changes only", "A3530001"]) {
    assert.match(browser, new RegExp(required, "i"));
  }
  for (const required of ["create_save", "stale_revision", "validation_error", "mediacat_activation_error", "explicit_activate", "edit_save", "delete_save", "baseline_bytes_restored"]) {
    assert.match(lifecycle, new RegExp(required));
  }
});
