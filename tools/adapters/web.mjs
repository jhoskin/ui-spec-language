// Web adapter: fires intents, advances the clock and observes the web build.
// It binds intents as spec/modality/web.md says (WEB-1, WEB-4, WEB-5, WEB-12).
// It holds no expectations.
import { chromium } from "playwright";
import { serve } from "../lib/serve.mjs";

const ARROWS = { up: "ArrowUp", down: "ArrowDown", left: "ArrowLeft", right: "ArrowRight", first: "Home", last: "End" };

// WEB-1: a person is the first name in lower case with no accent; Unassigned is "none".
const personId = (name) =>
  name === "Unassigned" ? "none" : name.split(" ")[0].normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

/** The observation of the page, by the roles of WEB-5. Runs in the page. */
function snapshot() {
  const text = (el) => [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.data).join("").trim();
  const nameOf = (el) => el.getAttribute("aria-label") ?? el.textContent.trim();
  const groupOf = (el) =>
    el.parentElement?.closest('[role="group"], [role="radiogroup"]')?.getAttribute("aria-label") ?? null;
  const roleOf = (el) => {
    const tag = el.tagName;
    const role = el.getAttribute("role");
    if (tag === "H1") return "place title";
    if (tag === "H2") return "heading";
    if (tag === "A") return el.textContent.startsWith("←") ? "up-link" : "link";
    if (role === "radio") return "choice";
    if (tag === "INPUT" && el.type === "checkbox") return "toggle";
    if (tag === "BUTTON") return el.hasAttribute("aria-pressed") ? "toggle" : "action";
    if (tag === "INPUT" || tag === "TEXTAREA") return "field";
    if (role === "group" && /^SL-\d+ /.test(el.getAttribute("aria-label") ?? "")) return "card";
    if (role === "alert") return "alert";
    if (role === "status") return "status line";
    return null;
  };
  const stateOf = (el, role) => {
    if (role === "toggle") {
      if (el.type === "checkbox") return el.checked ? "on" : "off";
      return { true: "on", false: "off", mixed: "mixed" }[el.getAttribute("aria-pressed")];
    }
    if (role === "choice") return el.getAttribute("aria-checked") === "true" ? "chosen" : "not chosen";
    return null;
  };
  const describe = (el) => {
    const role = roleOf(el);
    if (!role) return null;
    const name = role === "card" ? el.getAttribute("aria-label").split(" ")[0] : nameOf(el);
    return {
      role,
      name,
      group: groupOf(el),
      state: stateOf(el, role),
      disabled: el.disabled === true,
      text: role === "field" ? el.value : undefined,
    };
  };
  const parts = [
    ...document.querySelectorAll('h1, h2, a, button, input, textarea, [role="radio"], [role="alert"], [role="status"]'),
  ]
    .filter((el) => !el.closest('[role="group"][aria-label^="SL-"]') && !el.closest('[aria-label="Notice"]'))
    .map(describe).filter(Boolean);
  const texts = [...document.querySelectorAll("body *")].filter((el) => !el.closest('[aria-hidden="true"]')).map(text)
    .filter(Boolean);
  const cardOf = (el) => ({
    id: el.getAttribute("aria-label").split(" ")[0],
    selected: el.querySelector('input[type="checkbox"]').checked,
    marks: [...el.querySelectorAll(".mark")].map((m) => m.textContent),
    inView: el.getBoundingClientRect().top >= 0 && el.getBoundingClientRect().bottom <= innerHeight,
  });
  const columns = [...document.querySelectorAll("main section[aria-label]")].filter((s) => s.querySelector("h2")).map((
    s,
  ) => ({
    name: s.getAttribute("aria-label"),
    cards: [...s.querySelectorAll('[role="group"][aria-label^="SL-"]')].map((c) => cardOf(c).id),
  }));
  const cards = [...document.querySelectorAll('[role="group"][aria-label^="SL-"]')].map(cardOf);
  const box = document.querySelector('[aria-label="Notice"]');
  const notice = box
    ? {
      kind: box.getAttribute("role") === "alert" ? "error" : "info",
      text: box.querySelector("span").textContent,
      action: [...box.querySelectorAll("button")].map((b) => b.textContent).find((t) => t !== "Dismiss") ?? null,
    }
    : null;
  if (notice?.kind === "error") {
    parts.push({ role: "action", name: "Dismiss", group: null, state: null, disabled: false });
  }
  const a = document.activeElement;
  const focus = !a || a === document.body ? null : describe(a) ?? { role: "other", name: nameOf(a) };
  return {
    title: document.querySelector("h1")?.textContent ?? null,
    address: location.hash,
    depth: history.length,
    scrollTop: scrollY === 0,
    focus: focus && { role: focus.role, name: focus.name },
    parts,
    texts,
    columns,
    cards,
    notice,
    requests: globalThis.__slate.requests(),
    said: globalThis.__slate.announcements.length,
    announcements: [...globalThis.__slate.announcements],
  };
}

export async function createWebAdapter() {
  const server = await serve();
  const browser = await chromium.launch();
  let context = null;
  let page = null;
  let heard = 0;

  const ready = () => page.waitForFunction(() => globalThis.__slate && !globalThis.__slate.busy());
  const card = (id) => page.locator(`[role="group"][aria-label^="${id} "]`);
  const button = (name, group) =>
    (group ? page.getByRole("group", { name: group, exact: true }) : page).getByRole("button", { name, exact: true });
  const field = (name) => page.getByRole(name === "Filter cards" ? "searchbox" : "textbox", { name, exact: true });
  const focusedCard = () =>
    page.evaluate(() => document.activeElement?.getAttribute("aria-label")?.split(" ")[0] ?? null);

  // WEB-1: the written form of an address.
  const addressOf = (p) => {
    if (p.place === "card") return `#/card/${p.id}`;
    const q = [];
    if (p.text) q.push(`q=${encodeURIComponent(p.text).replace(/%20/g, "+")}`);
    if (p.labels.length) q.push(`labels=${p.labels.join(",")}`);
    if (p.assignees.length) q.push(`who=${p.assignees.map(personId).join(",")}`);
    return q.length ? `#/?${q.join("&")}` : "#/";
  };

  async function pointerTarget(column, position) {
    const region = page.getByRole("region", { name: column, exact: true });
    const carried = await page.evaluate(() =>
      document.querySelector(".card.carried")?.getAttribute("aria-label") ?? null
    );
    const boxes = [];
    for (const c of await region.locator('[role="group"][aria-label^="SL-"]').all()) {
      if ((await c.getAttribute("aria-label")) !== carried) boxes.push(await c.boundingBox());
    }
    const col = await region.boundingBox();
    const x = col.x + col.width / 2;
    if (!boxes.length) return { x, y: col.y + col.height - 10 };
    if (position <= 1) return { x, y: boxes[0].y + 2 };
    const above = boxes[Math.min(position - 1, boxes.length) - 1];
    return { x, y: above.y + above.height - 2 };
  }

  const fire = {
    "open-home": () => page.getByRole("link", { name: "Slate", exact: true }).click(),
    "go-back": () => page.goBack(),
    "go-forward": () => page.goForward(),
    reload: async () => {
      await page.reload();
      heard = 0;
    },
    "enter-address": ([raw]) => page.evaluate((h) => (location.hash = h), raw),
    dismiss: () => page.keyboard.press("Escape"),
    undo: () => page.keyboard.press("Control+z"),
    "notice-action": () => page.locator('[aria-label="Notice"] button').first().click(),
    "dismiss-notice": () => button("Dismiss").click(),
    "retry-place": () => button("Try again").click(),
    "ask-filter": () => page.keyboard.press("/"),
    "change-filter-text": ([text]) => field("Filter cards").fill(text),
    "commit-filter": async () => {
      await field("Filter cards").focus();
      await page.keyboard.press("Enter");
    },
    "toggle-label-filter": ([label]) => button(label, "Labels").click(),
    "toggle-assignee-filter": ([name]) => button(name, "Assignee").click(),
    "clear-filters": async () => {
      const bar = button("Clear filters");
      await ((await bar.count()) ? bar : button("Show all cards")).click();
    },
    "focus-card": ([id]) => card(id).focus(),
    "move-focus": ([dir]) => page.keyboard.press(ARROWS[dir]),
    "open-card": async ([id], via) => {
      if (via === "pointer") return card(id).getByRole("link").click();
      if (id && (await focusedCard()) !== id) await card(id).focus();
      await page.keyboard.press("Enter");
    },
    "toggle-select": async ([id], via) => {
      if (via === "pointer") return card(id).getByRole("checkbox").click();
      if (id) await card(id).focus();
      await page.keyboard.press("x");
    },
    "select-column": ([name]) => button(`Select all in ${name}`).click(),
    "clear-selection": () => button("Clear selection").click(),
    "bulk-move": ([name]) => button(name, "Move selected to").click(),
    "bulk-label": ([label]) => button(label, "Label selected").click(),
    "pick-up": async ([id], via) => {
      if (via === "pointer") {
        const box = await card(id).boundingBox();
        await page.mouse.move(box.x + 40, box.y + 8);
        await page.mouse.down();
        await page.mouse.move(box.x + 46, box.y + 14, { steps: 2 });
        return;
      }
      if (id) await card(id).focus();
      await page.keyboard.press("Space");
    },
    carry: ([dir]) => page.keyboard.press(ARROWS[dir]),
    "carry-to": async ([column, position]) => {
      // The layout moves as the card moves, so aim again until the pointer is on the target.
      for (let i = 0; i < 3; i++) {
        const t = await pointerTarget(column, Number(position));
        await page.mouse.move(t.x, t.y, { steps: 3 });
      }
    },
    drop: (_, via) => (via === "pointer" ? page.mouse.up() : page.keyboard.press("Space")),
    "cancel-carry": async (_, via) => {
      if (via !== "pointer") return page.keyboard.press("Escape");
      await page.mouse.move(600, 20, { steps: 3 });
      await page.mouse.up();
    },
    "delete-card": async ([id]) => {
      const onCardPlace = await button("Delete card").count();
      if (onCardPlace) return button("Delete card").click();
      if (id) await card(id).focus();
      await page.keyboard.press("Delete");
    },
    "retry-column": ([name]) => button(`Retry ${name}`).click(),
    "go-up": () => page.getByRole("link", { name: "← Board", exact: true }).click(),
    "edit-title": () => button("Edit title").click({ timeout: 2000 }).catch(() => {}),
    "change-title-text": ([text]) => field("Title").fill(text),
    "commit-title": () => page.keyboard.press("Enter"),
    "leave-title": () => page.keyboard.press("Tab"),
    "toggle-label": ([label]) => button(label, "Labels").click({ force: true, timeout: 2000 }).catch(() => {}),
    "choose-assignee": ([name]) => page.getByRole("radio", { name, exact: true }).click(),
    "edit-description": () => button("Edit description").click(),
    "change-description-text": ([text]) => field("Description").fill(text),
    "commit-description": () => button("Save").click(),
    "cancel-description": () => button("Cancel").click(),
    "change-comment-text": ([text]) => field("Add a comment").fill(text),
    "commit-comment": () => button("Add comment").click(),
    "retry-comments": () => button("Retry").click(),
    "open-board-link": () => page.getByRole("link", { name: "Go to the board", exact: true }).click(),
  };

  return {
    modality: "web",
    capabilities: ["pointer", "keys", "graphic"],
    addressOf,
    async start({ profile, at }) {
      await context?.close();
      context = await browser.newContext({ viewport: { width: 1500, height: 900 } });
      page = await context.newPage();
      page.setDefaultTimeout(5000);
      await page.addInitScript((p) => (globalThis.__slateHarness = { clock: "manual", profile: p }), profile);
      await page.goto(server.url + (at.raw ?? addressOf(at)));
      heard = 0;
      await ready();
    },
    async advance(ms) {
      await page.evaluate((n) => globalThis.__slate.advance(n), ms);
    },
    async fire(intent, args, via) {
      if (!fire[intent]) throw new Error(`the web adapter has no binding for ${intent}`);
      await fire[intent](args, via);
      await ready();
    },
    async observe() {
      await ready();
      const o = await page.evaluate(snapshot);
      o.announcements = o.announcements.slice(heard);
      heard = o.said;
      delete o.said;
      return o;
    },
    async close() {
      await context?.close();
      await browser.close();
      await server.close();
    },
  };
}
