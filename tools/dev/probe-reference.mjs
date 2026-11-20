#!/usr/bin/env node
// Extraction step 6: drive the running reference build with injected faults and
// record, after each action, the address, history depth, focus, scroll and notice.
// The output is evidence for the specification author. It is not a test.
import { chromium } from "playwright";
import { serve } from "../lib/serve.mjs";

const server = await serve();
const browser = await chromium.launch();
const lines = [];
const log = (s) => lines.push(s);

async function session(name, { hash = "#/", profile = "default", height = 900 } = {}, body) {
  const context = await browser.newContext({ viewport: { width: 1500, height } });
  const page = await context.newPage();
  await page.addInitScript((p) => (globalThis.__slateHarness = { clock: "manual", profile: p }), profile);
  await page.goto(server.url + hash);
  await page.waitForFunction(() => globalThis.__slate);
  let seen = 0;
  const snap = async () => {
    await page.waitForFunction(() => !globalThis.__slate.busy());
    const s = await page.evaluate((from) => {
      const a = document.activeElement;
      const f = !a || a === document.body
        ? "none"
        : `${a.getAttribute("role") ?? a.tagName.toLowerCase()} "${
          (a.getAttribute("aria-label") ?? a.textContent).slice(0, 40)
        }"`;
      return {
        hash: location.hash,
        depth: history.length,
        f,
        y: scrollY,
        notice: document.querySelector("#notice")?.innerText.replace(/\n/g, " | ") ?? "",
        said: globalThis.__slate.announcements.slice(from),
        n: globalThis.__slate.announcements.length,
        title: document.title,
      };
    }, seen);
    seen = s.n;
    return s;
  };
  const step = async (label, fn) => {
    await fn?.();
    const s = await snap();
    log(`  ${label}`);
    log(
      `      address ${s.hash || "(none)"} depth ${s.depth} focus ${s.f} scrollY ${s.y}` +
        (s.notice ? ` notice [${s.notice}]` : "") + (s.said.length ? ` said ${JSON.stringify(s.said)}` : ""),
    );
  };
  const t = {
    page,
    step,
    adv: (ms) => page.evaluate((n) => globalThis.__slate.advance(n), ms),
    key: (k) => page.keyboard.press(k),
    card: (id) => page.locator(`[data-card="${id}"]`),
    cards: (name) =>
      page.getByRole("region", { name, exact: true }).locator("[data-card]").evaluateAll((e) =>
        e.map((x) => x.dataset.card).join(" ")
      ),
  };
  log(`\n## ${name}`);
  await body(t);
  await context.close();
}

await session("First paint and Tab order on the board", {}, async (t) => {
  await t.step("first paint");
  await t.step("advance 400", () => t.adv(400));
  await t.step("advance 1800", () => t.adv(1800));
  for (let i = 1; i <= 16; i++) await t.step(`Tab ${i}`, () => t.key("Tab"));
});

await session("Pointer on a card", {}, async (t) => {
  await t.adv(2200);
  await t.step("click the card body of SL-104", () => t.card("SL-104").click({ position: { x: 200, y: 4 } }));
  await t.step("click the check box of SL-105", () => t.card("SL-105").getByRole("checkbox").click());
  await t.step("key x", () => t.key("x"));
  await t.step("Tab", () => t.key("Tab"));
  await t.step("Shift+Tab", () => t.key("Shift+Tab"));
  await t.step("click the title of SL-104", () => t.card("SL-104").getByRole("link").click());
  await t.step("browser Back", () => t.page.goBack());
  await t.step("browser Forward", () => t.page.goForward());
  await t.step("reload", async () => {
    await t.page.reload();
    await t.page.waitForFunction(() => globalThis.__slate);
    await t.adv(400);
  });
  await t.step("click up-link", () => t.page.getByRole("link", { name: "← Board" }).click());
  await t.step("advance 2200", () => t.adv(2200));
});

await session("Drag, Escape during a drag, drop outside", {}, async (t) => {
  await t.adv(2200);
  const box = await t.card("SL-102").boundingBox();
  const to = await t.card("SL-118").boundingBox();
  await t.page.mouse.move(box.x + 40, box.y + 8);
  await t.page.mouse.down();
  await t.page.mouse.move(to.x + 40, to.y + 2, { steps: 6 });
  await t.step(`drag SL-102 over In progress top: ${await t.cards("In progress")}`);
  await t.step("Escape", () => t.key("Escape"));
  await t.page.mouse.up();
  await t.step(`pointer up: Backlog ${await t.cards("Backlog")}`);
  await t.page.mouse.move(box.x + 40, box.y + 8);
  await t.page.mouse.down();
  await t.page.mouse.move(700, 60, { steps: 6 });
  await t.page.mouse.up();
  await t.step(`drop on the filter bar: Backlog ${await t.cards("Backlog")}`);
});

await session("Scroll and Back, short window", { height: 420 }, async (t) => {
  await t.adv(2200);
  await t.step("focus SL-109 by keys", async () => {
    await t.card("SL-101").focus();
    for (let i = 0; i < 8; i++) await t.key("ArrowDown");
  });
  await t.step("open (Enter)", () => t.key("Enter"));
  await t.step("go up (Escape)", () => t.key("Escape"));
  await t.step("header link on the unfiltered board", () => t.page.getByRole("link", { name: "Slate" }).click());
  await t.step("type a filter", async () => {
    await t.key("/");
    await t.page.keyboard.type("api");
    await t.adv(250);
  });
  await t.step("header link on the filtered board", () => t.page.getByRole("link", { name: "Slate" }).click());
  await t.step("browser Back", () => t.page.goBack());
  await t.step("enter address #/card/SL-126", () => t.page.evaluate(() => (location.hash = "#/card/SL-126")));
  await t.step("go up (Escape)", () => t.key("Escape"));
  await t.step("enter address #/nowhere", () => t.page.evaluate(() => (location.hash = "#/nowhere")));
  await t.step("browser Back", () => t.page.goBack());
});

await session("Notice and focus", {}, async (t) => {
  await t.adv(2200);
  await t.card("SL-101").focus();
  await t.step("Delete on SL-101", () => t.key("Delete"));
  await t.step("focus Undo, then advance 8000", async () => {
    await t.page.getByRole("button", { name: "Undo" }).focus();
    await t.adv(8000);
  });
  await t.step("advance 400", () => t.adv(400));
  await t.card("SL-107").focus();
  await t.step("carry SL-107 right and drop", async () => {
    await t.key("Space");
    await t.key("ArrowRight");
    await t.key("Space");
  });
  await t.step("advance 400 (move fails)", () => t.adv(400));
  await t.step("click Dismiss", () => t.page.getByRole("button", { name: "Dismiss" }).click());
  await t.step("Control+z with no notice", () => t.key("Control+z"));
});

await session("Card place by keys", { hash: "#/card/SL-120" }, async (t) => {
  await t.step("first paint");
  await t.step("advance 400", () => t.adv(400));
  await t.step("advance 300 (comments fail)", () => t.adv(300));
  for (let i = 1; i <= 6; i++) await t.step(`Tab ${i}`, () => t.key("Tab"));
  await t.step("click Edit title, then Escape", async () => {
    await t.page.getByRole("button", { name: "Edit title" }).click();
    await t.key("Escape");
  });
  await t.step("click Edit description, type, click the heading", async () => {
    await t.page.getByRole("button", { name: "Edit description" }).click();
    await t.page.keyboard.type("draft");
    await t.page.getByRole("heading", { name: "Comments" }).click();
  });
  await t.step("Escape with focus on the body", () => t.key("Escape"));
});

console.log(lines.join("\n"));
await browser.close();
await server.close();
