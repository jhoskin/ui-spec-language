// A test rig: the app with a manual clock, the real service double and a fake history.
import { readFileSync } from "node:fs";
import { createApp } from "../src/app.js";
import { createManualClock } from "../src/double/clock.js";
import { createService } from "../src/double/service.js";

const root = new URL("../../fixture/", import.meta.url);
export const data = JSON.parse(readFileSync(new URL("data.json", root)));
export const config = JSON.parse(readFileSync(new URL("service.json", root)));

export function rig({ address = "#/", profile = "default" } = {}) {
  const clock = createManualClock(Date.parse(config.clockStart));
  const service = createService({ data, config, profile, clock });
  const hist = { entries: [{ address, state: null }], at: 0 };
  let app = null;
  const nav = {
    address: () => hist.entries[hist.at].address,
    state: () => hist.entries[hist.at].state,
    push(a, state) {
      hist.entries.length = hist.at + 1;
      hist.entries.push({ address: a, state });
      hist.at += 1;
    },
    replace(a, state) {
      hist.entries[hist.at] = { address: a, state };
    },
    back() {
      if (hist.at === 0) return;
      hist.at -= 1;
      app.popped();
    },
  };
  const fx = { focus: null, scroll: null, announce: [] };
  app = createApp({
    clock,
    service,
    nav,
    onChange() {
      const e = app.takeEffects();
      if (e.focus) fx.focus = e.focus;
      if (e.scroll) fx.scroll = e.scroll;
      fx.announce.push(...e.announce);
    },
  });
  const t = {
    app,
    clock,
    service,
    hist,
    fx,
    nav,
    m: () => app.model(),
    forward() {
      hist.at += 1;
      app.popped();
    },
    enter(a) {
      nav.push(a, null);
      app.popped();
    },
    col: (id) => app.model().columns.find((c) => c.id === id),
    ids: (id) => t.col(id).cards.map((c) => c.id),
    ops: () => service.log.map((r) => r.op),
    ready() {
      app.start();
      clock.advance(1800 + 400);
      return t;
    },
  };
  return t;
}
