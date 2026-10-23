import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import test from "node:test";

const workflow = fs.readFileSync(".github/workflows/astv-353-disposable-staging.yml", "utf8");
const catalogue = fs.readFileSync("06_Validation/Staging/ASTV-353/config/astv/astv_intent_catalogue.yaml", "utf8");
const mapping = fs.readFileSync("06_Validation/Staging/ASTV-353/config/AdvNFC/advnfc_tag_mapping.yaml", "utf8");
const browser = fs.readFileSync("06_Validation/Staging/ASTV-353/browser/browser.spec.mjs", "utf8");
const lifecycle = fs.readFileSync("06_Validation/Staging/ASTV-353/config/staging/lifecycle.py", "utf8");
const prepareStage = fs.readFileSync("06_Validation/Staging/ASTV-353/config/staging/prepare_stage.py", "utf8");

const sha256 = (path) => crypto.createHash("sha256").update(fs.readFileSync(path)).digest("hex");

test("workflow is manual-only pending a separate execution gate and always disposes resources", () => {
  assert.match(workflow, /workflow_dispatch:/);
  assert.doesNotMatch(workflow, /pull_request:/);
  assert.doesNotMatch(workflow, /pull_request_target:/);
  assert.doesNotMatch(workflow, /\n\s+(push|schedule):/);
  assert.match(workflow, /ASTV-353-G2/);
  assert.match(workflow, /github\.event_name == 'workflow_dispatch'/);
  assert.match(workflow, /EFFECTIVE_MODE: \$\{\{ inputs\.mode \}\}/);
  assert.match(workflow, /github\.event_name == 'workflow_dispatch' && inputs\.mode == 'controlled_lifecycle'/);
  assert.match(workflow, /docker network create --internal/);
  assert.doesNotMatch(workflow, /^\s+(--publish|-p\s)/m);
  assert.match(workflow, /if: always\(\)/);
  assert.match(workflow, /docker rm --force/);
  assert.match(workflow, /docker network rm/);
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
  assert.match(browser, /getByRole\("heading", \{ name: "Intent Catalogue" \}\)/);
  assert.match(browser, /getByRole\("button", \{ name: "Add intent" \}\)/);
  assert.match(workflow, /docker network create --internal/);
  assert.match(workflow, /--cap-drop ALL/);
  assert.match(workflow, /--security-opt no-new-privileges/);
  assert.match(workflow, /if: always\(\)/);
  assert.match(workflow, /containers_removed=true/);
  assert.match(workflow, /network_removed=true/);
});

test("browser and lifecycle suites cover the approved acceptance matrix", () => {
  for (const required of ["desktop", "mobile", "non-admin", "Add intent", "Save stages changes only", "A3530001"]) {
    assert.match(browser, new RegExp(required, "i"));
  }
  for (const required of ["create_save", "stale_revision", "validation_error", "mediacat_activation_error", "explicit_activate", "edit_save", "delete_save", "baseline_bytes_restored"]) {
    assert.match(lifecycle, new RegExp(required));
  }
});
