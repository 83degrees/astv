import fs from "node:fs";
import { test, expect } from "@playwright/test";

const session = JSON.parse(fs.readFileSync("/stage/staging/browser-session.json", "utf8"));
const evidenceDir = "/evidence";

async function login(page, [username, password]) {
  await page.goto(session.base_url, { waitUntil: "domcontentloaded" });
  await page.locator('input[name="username"]').fill(username);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: /log in/i }).click();
  await page.waitForURL(/\/lovelace|\/astv-intent-catalogue/, { timeout: 30000 });
}

async function openPanel(page) {
  await page.goto(`${session.base_url}/astv-intent-catalogue`);
  await expect(page.getByRole("heading", { name: "Intent Catalogue" })).toBeVisible({ timeout: 30000 });
}

test("administrator desktop and mobile surfaces retain stage/activate semantics", async ({ browser }) => {
  const desktop = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await desktop.newPage();
  await login(page, session.admin);
  await openPanel(page);
  await expect(page.getByText("Administrator · edits are staged")).toBeVisible();
  await expect(page.getByRole("button", { name: "Add intent" })).toBeVisible();
  await page.getByRole("button", { name: "Tags" }).click();
  await expect(page.getByText("A3530001")).toBeVisible();
  await page.screenshot({ path: `${evidenceDir}/desktop-tags.png`, fullPage: true });
  await page.getByRole("button", { name: "Status" }).click();
  await expect(page.getByText("Save stages changes only.")).toBeVisible();
  await page.screenshot({ path: `${evidenceDir}/desktop-status.png`, fullPage: true });
  await desktop.close();

  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const mobilePage = await mobile.newPage();
  await login(mobilePage, session.admin);
  await openPanel(mobilePage);
  await expect(mobilePage.getByText("3 of 3 intents")).toBeVisible();
  await mobilePage.screenshot({ path: `${evidenceDir}/mobile-intents.png`, fullPage: true });
  await mobile.close();
});
test("non-admin is authenticated read-only and backend rejects mutation", async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  await login(page, session.reader);
  await openPanel(page);
  await expect(page.getByText("Read only").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Add intent" })).toHaveCount(0);
  const result = await page.evaluate(async () => {
    const hass = document.querySelector("home-assistant")?.hass;
    try {
      await hass.callWS({
        type: "call_service",
        domain: "astv_intent_catalogue",
        service: "create_intent_record",
        service_data: { expected_revision: "denied", intent_id: "astv353_denied", record: {} },
        return_response: true,
      });
      return { rejected: false };
    } catch (error) {
      return { rejected: true, code: error.code ?? "unknown" };
    }
  });
  expect(result.rejected).toBe(true);
  await page.screenshot({ path: `${evidenceDir}/non-admin-read-only.png`, fullPage: true });
  fs.writeFileSync(`${evidenceDir}/permission.json`, JSON.stringify(result, null, 2) + "\n");
  await context.close();
});
test("known AdvNFC reference prevents deletion in the UI", async ({ browser }) => {
  test.skip(process.env.ASTV353_MODE !== "controlled_lifecycle", "Requires the separately authorised lifecycle gate");
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  await login(page, session.admin);
  await openPanel(page);
  await page.getByText("ASTV 353 referenced routine").click();
  await page.getByRole("button", { name: "Delete" }).click();
  await expect(page.getByText(/A3530001/)).toBeVisible();
  await expect(page.getByText(/referenced by AdvNFC/i)).toBeVisible();
  await page.screenshot({ path: `${evidenceDir}/referenced-delete-blocked.png`, fullPage: true });
  await context.close();
});
