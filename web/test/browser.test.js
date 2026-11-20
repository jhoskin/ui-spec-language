// End-to-end checks in a real browser: keys, pointer drag, focus and history.
import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { chromium } from "playwright";
import { serve } from "../../tools/lib/serve.mjs";

let server, browser;
before(async () => {
  server = await serve();
  browser = await chromium.launch();
});
after(async () => {
  await browser.close();
  await server.close();
});

async function open(hash = "#/", profile = "default") {
  const page = await (await browser.newContext({ viewport: { width: 1500, height: 900 } })).newPage();
  await page.addInitScript((p) => (globalThis.__slateHarness = { clock: "manual", profile: p }), profile);
  await page.goto(server.url + hash);
  await page.waitForFunction(() => globalThis.__slate);
  page.advance = (ms) => page.evaluate((n) => globalThis.__slate.advance(n), ms);
  page.focused = () =>
    page.evaluate(() => document.activeElement?.getAttribute("aria-label") ?? document.activeElement?.textContent);
  page.column = (name) =>
    page.getByRole("region", { name, exact: true }).locator("[data-card]").evaluateAll((els) =>
      els.map((e) => e.dataset.card)
    );
  page.settle = () => page.waitForFunction(() => !globalThis.__slate.busy());
  return page;
}

test("keys: move focus, carry, drop, undo", async () => {
  const page = await open();
  await page.advance(2200);
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  for (let i = 0; i < 30 && !(await page.focused()).startsWith("SL-101"); i++) await page.keyboard.press("Tab");
  assert.equal(await page.focused(), "SL-101 Export board as CSV");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Space");
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("ArrowRight");
  assert.equal(await page.getByText("Moving").count(), 1);
  await page.keyboard.press("Space");
  assert.deepEqual(await page.column("In progress"), ["SL-118", "SL-102", "SL-119"]);
  assert.equal(await page.focused(), "SL-102 Fix login redirect loop");
  await page.advance(400);
  assert.equal(await page.getByRole("status", { name: "Notice" }).innerText(), "Moved SL-102 to In progress.\nUndo");
  await page.keyboard.press("Control+z");
  assert.equal((await page.column("Backlog"))[1], "SL-102");
  assert.equal(await page.focused(), "SL-102 Fix login redirect loop");
  await page.close();
});

test("pointer drag gives the same move", async () => {
  const page = await open();
  await page.advance(2200);
  const from = await page.locator('[data-card="SL-103"]').boundingBox();
  const to = await page.locator('[data-card="SL-112"]').boundingBox();
  await page.mouse.move(from.x + 30, from.y + 10);
  await page.mouse.down();
  await page.mouse.move(from.x + 60, from.y + 20, { steps: 3 });
  await page.mouse.move(to.x + 30, to.y + to.height - 4, { steps: 5 });
  await page.mouse.up();
  assert.deepEqual((await page.column("Ready")).slice(0, 3), ["SL-111", "SL-112", "SL-103"]);
  assert.equal(new URL(page.url()).hash, "#/");
  await page.advance(400);
  assert.match(await page.locator("#notice").innerText(), /Moved SL-103 to Ready\./);
  await page.close();
});

test("history: open adds an entry, Escape goes Back to the card, filter rewrites", async () => {
  const page = await open();
  await page.advance(2200);
  const depth = () => page.evaluate(() => history.length);
  const d0 = await depth();
  await page.keyboard.press("/");
  await page.keyboard.type("webhook");
  await page.advance(250);
  assert.equal(new URL(page.url()).hash, "#/?q=webhook");
  assert.equal(await depth(), d0);
  await page.keyboard.press("Enter");
  assert.equal(await page.focused(), "SL-112 Document the webhook API");
  await page.keyboard.press("Enter");
  assert.equal(new URL(page.url()).hash, "#/card/SL-112");
  assert.equal(await depth(), d0 + 1);
  assert.equal(await page.focused(), "Document the webhook API");
  assert.equal(await page.title(), "SL-112 Document the webhook API · Slate");
  await page.keyboard.press("Escape");
  await page.settle();
  assert.equal(new URL(page.url()).hash, "#/?q=webhook");
  assert.equal(await page.focused(), "SL-112 Document the webhook API");
  await page.goForward();
  await page.settle();
  await page.getByRole("button", { name: "Delete card" }).click();
  await page.settle();
  assert.equal(await page.focused(), "Board");
  assert.match(await page.locator("#notice").innerText(), /Deleted SL-112\./);
  await page.reload();
  await page.waitForFunction(() => globalThis.__slate);
  await page.advance(2200);
  assert.deepEqual(await page.column("Ready"), ["SL-112"]);
  await page.close();
});

test("card place: title edit by keys, blur saves, focus falls back to the title", async () => {
  const page = await open("#/card/SL-105");
  await page.advance(400);
  await page.getByRole("button", { name: "Edit title" }).click();
  await page.keyboard.type("Write the onboarding guide");
  await page.keyboard.press("Enter");
  assert.equal(await page.focused(), "Write the onboarding guide");
  assert.equal(await page.getByText("Saving…").count(), 1);
  await page.advance(400);
  assert.equal(await page.getByText("Saving…").count(), 0);
  await page.getByRole("button", { name: "Edit title" }).click();
  await page.keyboard.type("Left by Tab");
  await page.keyboard.press("Tab");
  assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "Left by Tab");
  await page.close();
});
