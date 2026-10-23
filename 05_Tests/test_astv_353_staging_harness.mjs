import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const workflow = fs.readFileSync(".github/workflows/astv-353-disposable-staging.yml", "utf8");
const catalogue = fs.readFileSync("06_Validation/Staging/ASTV-353/config/astv/astv_intent_catalogue.yaml", "utf8");
const mapping = fs.readFileSync("06_Validation/Staging/ASTV-353/config/AdvNFC/advnfc_tag_mapping.yaml", "utf8");
const browser = fs.readFileSync("06_Validation/Staging/ASTV-353/browser/browser.spec.mjs", "utf8");
const lifecycle = fs.readFileSync("06_Validation/Staging/ASTV-353/config/staging/lifecycle.py", "utf8");

test("workflow is manual, human-gated, internally networked, and unconditionally disposed", () => {
  assert.match(workflow, /workflow_dispatch:/);
  assert.doesNotMatch(workflow, /\n\s+(push|pull_request|schedule):/);
  assert.match(workflow, /ASTV-353-G2/);
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
