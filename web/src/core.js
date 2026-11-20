// Pure rules of Slate: addresses, filters, text formats and position arithmetic.
// Nothing here reads the clock, the service or the page.

export const LABEL_LIMIT = 3;
export const TITLE_MAX = 80;

/** Collapse runs of white space to one space and trim. */
export function squash(text) {
  return String(text ?? "").replace(/\s+/g, " ").trim();
}

export function emptyFilter() {
  return { q: "", labels: [], who: [] };
}

export function filterActive(f) {
  return f.q !== "" || f.labels.length > 0 || f.who.length > 0;
}

/**
 * Parse the part of an address after "#".
 * @returns {{place: "board", filter: object} | {place: "card", id: string} | {place: "missing"}}
 */
export function parseAddress(hash) {
  let rest = String(hash ?? "").replace(/^#/, "");
  if (rest === "" || rest === "/") return { place: "board", filter: emptyFilter() };
  if (!rest.startsWith("/")) return { place: "missing" };
  let query = "";
  const at = rest.indexOf("?");
  if (at >= 0) {
    query = rest.slice(at + 1);
    rest = rest.slice(0, at);
  }
  if (rest === "/") {
    const filter = emptyFilter();
    for (const part of query.split("&")) {
      const eq = part.indexOf("=");
      if (eq < 0) continue;
      const key = part.slice(0, eq);
      let value;
      try {
        value = decodeURIComponent(part.slice(eq + 1).replace(/\+/g, " "));
      } catch {
        continue;
      }
      if (key === "q") filter.q = squash(value);
      else if (key === "labels") filter.labels = value.split(",").filter(Boolean);
      else if (key === "who") filter.who = value.split(",").filter(Boolean);
    }
    return { place: "board", filter };
  }
  const m = /^\/card\/([^/]+)$/.exec(rest);
  if (m) return { place: "card", id: m[1].toUpperCase() };
  return { place: "missing" };
}

/**
 * Put a filter in its one written form: known values only, in the fixed order.
 * `meta` is null while the board data is not loaded; then values are kept as they are.
 */
export function canonicalFilter(filter, meta) {
  const uniq = (list) => [...new Set(list)];
  if (!meta) return { q: squash(filter.q), labels: uniq(filter.labels), who: uniq(filter.who) };
  const people = [...meta.people.map((p) => p.id), "none"];
  return {
    q: squash(filter.q),
    labels: meta.labels.filter((l) => filter.labels.includes(l)),
    who: people.filter((p) => filter.who.includes(p)),
  };
}

export function formatAddress(route) {
  if (route.place === "card") return `#/card/${route.id}`;
  if (route.place !== "board") return route.raw ?? "#/";
  const f = route.filter;
  const parts = [];
  if (f.q) parts.push(`q=${encodeURIComponent(f.q).replace(/%20/g, "+")}`);
  if (f.labels.length) parts.push(`labels=${f.labels.join(",")}`);
  if (f.who.length) parts.push(`who=${f.who.join(",")}`);
  return parts.length ? `#/?${parts.join("&")}` : "#/";
}

/** Text: every word occurs in the title or the identifier. Labels: all. Assignee: any. */
export function matchesFilter(card, f) {
  if (f.q) {
    const hay = `${card.title} ${card.id}`.toLowerCase();
    for (const word of f.q.toLowerCase().split(" ")) if (!hay.includes(word)) return false;
  }
  for (const l of f.labels) if (!card.labels.includes(l)) return false;
  if (f.who.length && !f.who.includes(card.assignee ?? "none")) return false;
  return true;
}

export function countText(n, noun) {
  return `${n} ${noun}${n === 1 ? "" : "s"}`;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "20 Nov 2026, 09:14" in UTC. Never a relative time. */
export function formatTime(iso) {
  const d = new Date(iso);
  const two = (n) => String(n).padStart(2, "0");
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}, ${two(d.getUTCHours())}:${
    two(d.getUTCMinutes())
  }`;
}

/** Check a title after `squash`. Returns a message, or "" when the title is good. */
export function titleProblem(title) {
  if (title.length < 1) return "A title needs at least 1 character.";
  if (title.length > TITLE_MAX) return `A title can have at most ${TITLE_MAX} characters.`;
  return "";
}

/**
 * The absolute index for a card dropped at position `vIndex` among the visible cards.
 * `order` is the column without the carried card. At the visible top the card goes to
 * the absolute top. Elsewhere it goes directly after the visible card above it.
 */
export function dropIndex(order, visible, vIndex) {
  if (vIndex <= 0 || visible.length === 0) return 0;
  const anchor = visible[Math.min(vIndex, visible.length) - 1];
  return order.indexOf(anchor) + 1;
}

/** Sort labels into the fixed order of the board. */
export function sortLabels(labels, all) {
  return all.filter((l) => labels.includes(l));
}
