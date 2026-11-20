// Clocks for the fixture. The application reads time and sets timers only
// through one of these, so that an adapter can control time (FIX: controlled clock).

/**
 * A clock that moves only when `advance` is called.
 * Timers run in order of due time, then in order of creation.
 */
export function createManualClock(startMs) {
  let now = startMs;
  let nextId = 1;
  const timers = new Map();
  return {
    kind: "manual",
    now: () => now,
    setTimeout(fn, ms) {
      const id = nextId++;
      timers.set(id, { due: now + Math.max(0, ms), fn, id });
      return id;
    },
    clearTimeout(id) {
      timers.delete(id);
    },
    advance(ms) {
      const end = now + ms;
      for (;;) {
        let next = null;
        for (const t of timers.values()) {
          if (t.due <= end && (!next || t.due < next.due || (t.due === next.due && t.id < next.id))) next = t;
        }
        if (!next) break;
        timers.delete(next.id);
        now = next.due;
        next.fn();
      }
      now = end;
    },
    pending: () => timers.size,
  };
}

/** A clock that follows real time but starts at the fixture start time. */
export function createRealClock(startMs) {
  const origin = Date.now();
  return {
    kind: "real",
    now: () => startMs + (Date.now() - origin),
    setTimeout: (fn, ms) => globalThis.setTimeout(fn, ms),
    clearTimeout: (id) => globalThis.clearTimeout(id),
  };
}
