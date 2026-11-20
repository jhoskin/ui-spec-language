// Start-up: load the fixture, build the clock and the service double, start the app.
// An adapter can set `window.__slateHarness = { clock: "manual", profile }` before load.

import { createApp } from "./app.js";
import { createManualClock, createRealClock } from "./double/clock.js";
import { createService } from "./double/service.js";
import { createView } from "./view.js";

const harness = globalThis.__slateHarness ?? {};
const [data, config] = await Promise.all([
  fetch("../fixture/data.json").then((r) => r.json()),
  fetch("../fixture/service.json").then((r) => r.json()),
]);
const start = Date.parse(config.clockStart);
const clock = harness.clock === "manual" ? createManualClock(start) : createRealClock(start);
const service = createService({ data, config, profile: harness.profile ?? "default", clock });

history.scrollRestoration = "manual";
const nav = {
  address: () => location.hash || "#/",
  state: () => history.state,
  push: (address, state) => history.pushState(state, "", address),
  replace: (address, state) => history.replaceState({ ...state, scroll: history.state?.scroll }, "", address),
  back: () => history.back(),
};

let view = null;
const app = createApp({ clock, service, nav, onChange: () => view?.paint() });
view = createView(app, document);
addEventListener("popstate", () => app.popped());
app.start();

// What an adapter may use. It gives control of time and a count of requests,
// and nothing about what the page shows.
globalThis.__slate = {
  advance: (ms) => clock.advance(ms),
  requests: () => service.log.map((r) => ({ op: r.op, at: r.at - start })),
  announcements: view.announcements,
  busy: () => app.holdPaint(),
};
