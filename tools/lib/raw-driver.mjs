// A raw driver for the reference build: web actions in, raw observations out.
// It has no intent layer and no expectations. Isolated roles use it through files:
// a role writes requests/<name>.json in its work directory, and the watcher writes
// results/<name>.json. Each request runs in a fresh browser context.
import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { chromium } from "playwright";
import { serve } from "./serve.mjs";

const locate = (page, t) => {
  if (t.card) return page.locator(`[data-card="${t.card}"]`);
  if (t.role) return page.getByRole(t.role, { name: t.name, exact: true }).first();
  return page.getByText(t.text, { exact: true }).first();
};

async function observe(page, seen) {
  await page.waitForFunction(() => globalThis.__slate && !globalThis.__slate.busy());
  const o = await page.evaluate((from) => {
    const a = document.activeElement;
    const said = globalThis.__slate.announcements;
    return {
      address: location.hash,
      historyLength: history.length,
      windowTitle: document.title,
      focus: !a || a === document.body ? null : {
        role: a.getAttribute("role") ?? a.tagName.toLowerCase(),
        name: a.getAttribute("aria-label") ?? a.textContent.trim().slice(0, 80),
        text: a.value ?? undefined,
      },
      scrollY: Math.round(scrollY),
      announcements: said.slice(from),
      said: said.length,
      requests: globalThis.__slate.requests(),
    };
  }, seen.n);
  seen.n = o.said;
  delete o.said;
  o.screen = await page.locator("body").ariaSnapshot();
  return o;
}

/** Run one request: { profile, start, viewport, steps: [...] }. */
export async function runRequest(browser, base, req) {
  const context = await browser.newContext({ viewport: req.viewport ?? { width: 1500, height: 900 } });
  const page = await context.newPage();
  await page.addInitScript(
    (p) => (globalThis.__slateHarness = { clock: "manual", profile: p }),
    req.profile ?? "default",
  );
  await page.goto(base + (req.start ?? "#/"));
  const seen = { n: 0 };
  const out = [{ step: "start", ...(await observe(page, seen)) }];
  for (const s of req.steps ?? []) {
    try {
      if (s.advance != null) await page.evaluate((n) => globalThis.__slate.advance(n), s.advance);
      else if (s.key) await page.keyboard.press(s.key);
      else if (s.type != null) await page.keyboard.type(s.type);
      else if (s.click) await locate(page, s.click).click(s.modifiers ? { modifiers: s.modifiers } : {});
      else if (s.focus) await locate(page, s.focus).focus();
      else if (s.fill) await locate(page, s.fill).fill(s.value ?? "");
      else if (s.pointer) {
        if (s.pointer === "up") await page.mouse.up();
        else {
          let x = s.x, y = s.y;
          if (s.on) {
            const box = await locate(page, s.on).boundingBox();
            x = box.x + Math.min(40, box.width / 2);
            y = s.at === "top" ? box.y + 3 : s.at === "bottom" ? box.y + box.height - 3 : box.y + box.height / 2;
          }
          if (s.pointer === "down") {
            await page.mouse.move(x, y);
            await page.mouse.down();
          } else await page.mouse.move(x, y, { steps: 5 });
        }
      } else if (s.back) await page.goBack();
      else if (s.forward) await page.goForward();
      else if (s.reload) {
        await page.reload();
        seen.n = 0;
      } else if (s.address) await page.evaluate((h) => (location.hash = h), s.address);
      else if (s.scrollTo != null) await page.evaluate((y) => scrollTo(0, y), s.scrollTo);
      else throw new Error("unknown step");
      out.push({ step: s, ...(await observe(page, seen)) });
    } catch (e) {
      out.push({ step: s, error: String(e.message).split("\n")[0] });
      break;
    }
  }
  await context.close();
  return out;
}

/** Watch `work/requests` and answer each request file one time. Returns a stop function. */
export async function watch(work) {
  const server = await serve();
  const browser = await chromium.launch();
  mkdirSync(join(work, "requests"), { recursive: true });
  mkdirSync(join(work, "results"), { recursive: true });
  let busy = false;
  const timer = setInterval(async () => {
    if (busy) return;
    busy = true;
    try {
      for (const f of readdirSync(join(work, "requests")).filter((x) => x.endsWith(".json")).sort()) {
        const to = join(work, "results", f);
        if (existsSync(to)) continue;
        let result;
        try {
          result = await runRequest(browser, server.url, JSON.parse(readFileSync(join(work, "requests", f), "utf8")));
        } catch (e) {
          result = { error: String(e.message) };
        }
        // Write, then rename, so that a reader never sees half a file.
        writeFileSync(`${to}.part`, `${JSON.stringify(result, null, 1)}\n`);
        renameSync(`${to}.part`, to);
      }
    } finally {
      busy = false;
    }
  }, 300);
  return async () => {
    clearInterval(timer);
    await browser.close();
    await server.close();
  };
}

if (import.meta.main) {
  const stop = await watch(process.argv[2]);
  process.on("SIGTERM", async () => {
    await stop();
    process.exit(0);
  });
}
