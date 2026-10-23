import fs from "node:fs";
import { test, expect } from "@playwright/test";
import {
  PANEL_PATH,
  classifyAuthenticationState,
  permissionProbeRequest,
  requireBackendUnauthorizedProof,
} from "./browser-contract.mjs";

const session = JSON.parse(fs.readFileSync("/stage/staging/browser-session.json", "utf8"));
const evidenceDir = "/evidence";
const boundedTimeout = 30000;

async function authenticatedState(page) {
  return page.evaluate(() => {
    const homeAssistant = document.querySelector("home-assistant");
    const error = [...document.querySelectorAll("ha-alert, [role=alert], .error")]
      .map((element) => element.textContent?.trim())
      .find(Boolean);
    return {
      authenticated: Boolean(homeAssistant?.hass?.user && typeof homeAssistant.hass.callWS === "function"),
      error: error ?? null,
    };
  });
}

async function login(page, [username, password]) {
  await page.goto(session.base_url, { waitUntil: "domcontentloaded", timeout: boundedTimeout });
  await page.locator('input[name="username"]').fill(username, { timeout: boundedTimeout });
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: /log in/i }).click();

  const deadline = Date.now() + boundedTimeout;
  while (Date.now() < deadline) {
    const state = await authenticatedState(page);
    const classification = classifyAuthenticationState(state);
    if (classification === "authenticated") return;
    if (classification === "authentication_error") throw new Error(`Home Assistant authentication failed: ${state.error}`);
    await page.waitForTimeout(250);
  }
  throw new Error(`Home Assistant authentication did not complete within ${boundedTimeout} ms (last URL: ${page.url()})`);
}

async function openPanel(page) {
  await page.goto(`${session.base_url}${PANEL_PATH}`, {
    waitUntil: "domcontentloaded",
    timeout: boundedTimeout,
  });
  await expect(page).toHaveURL(/\/astv-intent-catalogue\/?$/, { timeout: boundedTimeout });
  await expect.poll(async () => (await authenticatedState(page)).authenticated, {
    message: "authenticated Home Assistant client is available on the ASTV panel route",
    timeout: boundedTimeout,
  }).toBe(true);
  await expect(page.getByRole("heading", { name: "Intent Catalogue", level: 1 })).toBeVisible({ timeout: boundedTimeout });
}

test("administrator desktop and mobile surfaces retain stage/activate semantics", async ({ browser }) => {
  const desktop = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  try {
    const page = await desktop.newPage();
    await login(page, session.admin);
    await openPanel(page);
    await expect(page.getByText("Administrator · edits are staged")).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Intent Catalogue sections" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Add intent" })).toBeVisible();

    const search = page.getByRole("searchbox", { name: "Search" });
    const type = page.getByRole("combobox", { name: "Type" });
    const sort = page.getByRole("combobox", { name: "Sort" });
    await search.focus();
    await expect(search).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(type).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(sort).toBeFocused();

    const tags = page.getByRole("button", { name: "Tags" });
    await tags.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByText("A3530001")).toBeVisible();
    await page.screenshot({ path: `${evidenceDir}/desktop-tags.png`, fullPage: true });

    const status = page.getByRole("button", { name: "Status" });
    await status.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("heading", { name: "State and validation" })).toBeVisible();
    await expect(page.getByText("Save stages changes only.")).toBeVisible();
    await page.screenshot({ path: `${evidenceDir}/desktop-status.png`, fullPage: true });
  } finally {
    await desktop.close();
  }

  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 } });
  try {
    const mobilePage = await mobile.newPage();
    await login(mobilePage, session.admin);
    await openPanel(mobilePage);
    await expect(mobilePage.getByText("3 of 3 intents")).toBeVisible();
    await mobilePage.screenshot({ path: `${evidenceDir}/mobile-intents.png`, fullPage: true });
  } finally {
    await mobile.close();
  }
});

test("non-admin is authenticated read-only and backend rejects admin-only validation", async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  try {
    const page = await context.newPage();
    await login(page, session.reader);
    await openPanel(page);
    await expect(page.getByText("Read only").first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Add intent" })).toHaveCount(0);
    const result = await page.evaluate(async (request) => {
      const homeAssistant = document.querySelector("home-assistant");
      if (!homeAssistant?.hass) return { kind: "precondition_failure", reason: "missing_hass" };
      if (typeof homeAssistant.hass.callWS !== "function") return { kind: "precondition_failure", reason: "missing_callWS" };
      try {
        await homeAssistant.hass.callWS(request);
        return { kind: "unexpected_success" };
      } catch (error) {
        if (!error || typeof error !== "object") return { kind: "unexpected_exception", reason: typeof error };
        return { kind: "backend_denial", code: String(error.code ?? "") };
      }
    }, permissionProbeRequest());
    let verification;
    try {
      verification = requireBackendUnauthorizedProof(result);
    } catch (error) {
      fs.writeFileSync(`${evidenceDir}/permission.json`, JSON.stringify({ status: "failed", probe: result }, null, 2) + "\n");
      throw error;
    }
    fs.writeFileSync(`${evidenceDir}/permission.json`, JSON.stringify({
      status: verification.status,
      proof: verification.proof,
      probe: result,
    }, null, 2) + "\n");
    await page.screenshot({ path: `${evidenceDir}/non-admin-read-only.png`, fullPage: true });
  } finally {
    await context.close();
  }
});

test("known AdvNFC reference prevents deletion in the UI", async ({ browser }) => {
  test.skip(process.env.ASTV353_MODE !== "controlled_lifecycle", "Requires the separately authorised lifecycle gate");
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  try {
    const page = await context.newPage();
    await login(page, session.admin);
    await openPanel(page);
    await page.getByText("ASTV 353 referenced routine").click();
    await page.getByRole("button", { name: "Delete" }).click();
    await expect(page.getByText(/A3530001/)).toBeVisible();
    await expect(page.getByText(/referenced by AdvNFC/i)).toBeVisible();
    await page.screenshot({ path: `${evidenceDir}/referenced-delete-blocked.png`, fullPage: true });
  } finally {
    await context.close();
  }
});
