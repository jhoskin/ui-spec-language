// Slate application logic. It holds the session state and decides every
// user-visible effect. It does not touch the page: the view reads `model()` and
// `takeEffects()`, and the clock, the service and the history are injected.

import {
  canonicalFilter,
  countText,
  dropIndex,
  emptyFilter,
  filterActive,
  formatAddress,
  formatTime,
  LABEL_LIMIT,
  matchesFilter,
  parseAddress,
  sortLabels,
  squash,
  titleProblem,
} from "./core.js";

const FILTER_DELAY = 250;
const NOTICE_TIME = 8000;
const SLOW_MARK = 1000;

const blankUi = () => ({ editTitle: null, editDescription: null, commentDraft: "", commentError: "" });

/**
 * @param {{clock: object, service: object, nav: object, onChange: () => void}} env
 * `nav` gives address(), state(), push(address, state), replace(address, state), back().
 */
export function createApp({ clock, service, nav, onChange }) {
  const S = {
    route: null,
    meta: { status: "none", columns: [], people: [], labels: [], currentUser: null },
    columns: {},
    cards: {},
    deleted: new Set(),
    cardLoad: {},
    comments: {},
    sending: new Set(),
    filterDraft: "",
    filterTimer: null,
    lastFilter: null,
    selection: [],
    carry: null,
    notice: null,
    boardFocus: null,
    ui: blankUi(),
    pendingBack: false,
  };
  let effects = { focus: null, scroll: null, announce: [] };
  let depth = 0;

  // Every entry point runs inside `act`, so the view repaints once per change.
  function act(fn) {
    return (...args) => {
      depth += 1;
      try {
        return fn(...args);
      } finally {
        depth -= 1;
        if (depth === 0) onChange();
      }
    };
  }
  const later = (fn, ms) => clock.setTimeout(act(fn), ms);
  const request = (op, args, fn) => service.call(op, args, act(fn));
  const focus = (key) => (effects.focus = key);
  const announce = (text) => effects.announce.push(text);

  // ---------- data helpers ----------

  const metaReady = () => S.meta.status === "ready";
  const columnName = (id) => S.meta.columns.find((c) => c.id === id)?.name ?? id;
  const personName = (id) => S.meta.people.find((p) => p.id === id)?.name ?? "Unassigned";
  const boardFilter = () => (S.route?.place === "board" ? S.route.filter : emptyFilter());
  const allColumnsReady = () => metaReady() && S.meta.columns.every((c) => S.columns[c.id]?.status === "ready");
  const settled = () =>
    metaReady() && S.meta.columns.every((c) => ["ready", "failed"].includes(S.columns[c.id]?.status));
  const orderOf = (col) => S.columns[col]?.order ?? [];
  const visibleIn = (col, except) =>
    orderOf(col).filter((id) => id !== except && matchesFilter(S.cards[id], boardFilter()));
  const isVisible = (id) =>
    S.route?.place === "board" && !!S.cards[id] && !S.deleted.has(id) &&
    S.columns[S.cards[id].column]?.status === "ready" && orderOf(S.cards[id].column).includes(id) &&
    matchesFilter(S.cards[id], boardFilter());
  const boardOrder = (ids) => {
    const rank = (id) => {
      const col = S.meta.columns.findIndex((c) => c.id === S.cards[id].column);
      return col * 10000 + orderOf(S.cards[id].column).indexOf(id);
    };
    return [...ids].sort((a, b) => rank(a) - rank(b));
  };
  const firstVisible = () => {
    for (const c of S.meta.columns) {
      const v = visibleIn(c.id);
      if (v.length) return v[0];
    }
    return null;
  };
  const boardStop = () => (S.boardFocus && isVisible(S.boardFocus) ? S.boardFocus : firstVisible());
  const pruneSelection = () => (S.selection = S.selection.filter(isVisible));

  function place(id, column, index) {
    const from = orderOf(S.cards[id].column);
    const at = from.indexOf(id);
    if (at >= 0) from.splice(at, 1);
    const to = orderOf(column);
    to.splice(Math.min(Math.max(index, 0), to.length), 0, id);
    S.cards[id].column = column;
  }
  const positions = (ids) =>
    ids.map((id) => ({ card: id, column: S.cards[id].column, index: orderOf(S.cards[id].column).indexOf(id) }));
  // Put cards back at recorded positions: take all out, then insert in rising order.
  function restore(records) {
    const sorted = [...records].sort((a, b) =>
      a.column === b.column ? a.index - b.index : a.column < b.column ? -1 : 1
    );
    for (const r of sorted) {
      const from = orderOf(S.cards[r.card].column);
      const at = from.indexOf(r.card);
      if (at >= 0) from.splice(at, 1);
    }
    for (const r of sorted) {
      const to = orderOf(r.column);
      to.splice(Math.min(r.index, to.length), 0, r.card);
      S.cards[r.card].column = r.column;
    }
  }
  function addCard(c, column) {
    S.cards[c.id] = {
      id: c.id,
      title: c.title,
      description: c.description,
      labels: c.labels,
      assignee: c.assignee,
      comments: c.comments,
      column,
      pending: { move: 0, title: 0, description: 0, labels: 0, assignee: 0 },
    };
  }

  // ---------- notice ----------

  function endNotice(reason) {
    const n = S.notice;
    if (!n) return;
    if (n.timer != null) clock.clearTimeout(n.timer);
    S.notice = null;
    n.onEnd?.(reason);
  }
  function raise(kind, text, action, onEnd) {
    endNotice("replaced");
    const n = { kind, text, action: action ?? null, onEnd, timer: null };
    if (kind === "info") n.timer = later(() => S.notice === n && endNotice("timeout"), NOTICE_TIME);
    S.notice = n;
    announce(text);
  }

  // ---------- loading ----------

  function ensureMeta() {
    if (S.meta.status !== "none") return;
    S.meta.status = "loading";
    request("loadBoard", {}, (reply) => {
      if (!reply.ok) {
        S.meta.status = "failed";
        return;
      }
      S.meta = { status: "ready", ...reply.data };
      for (const c of S.meta.columns) S.columns[c.id] ??= { status: "none", order: [], slow: false };
      if (S.route.place === "board") {
        canonicalize();
        ensureColumns();
      } else cardShown();
    });
  }
  function loadColumn(id) {
    const col = S.columns[id];
    col.status = "loading";
    col.slow = false;
    const mark = later(() => col.status === "loading" && (col.slow = true), SLOW_MARK);
    request("loadColumn", { column: id }, (reply) => {
      clock.clearTimeout(mark);
      col.slow = false;
      if (!reply.ok) {
        col.status = "failed";
        return;
      }
      col.order = [];
      for (const c of reply.data.cards) {
        if (S.deleted.has(c.id)) continue;
        // Data that the session already holds wins over a later load.
        if (!S.cards[c.id]) addCard(c, id);
        S.cards[c.id].column = id;
        col.order.push(c.id);
      }
      col.status = "ready";
      if (settled() && S.route.place === "board") announce(countLine());
    });
  }
  function ensureColumns() {
    if (!metaReady()) return;
    for (const c of S.meta.columns) if (S.columns[c.id].status === "none") loadColumn(c.id);
  }
  function ensureCard(id) {
    if (S.cards[id] || S.deleted.has(id) || S.cardLoad[id] || allColumnsReady()) return;
    S.cardLoad[id] = "loading";
    request("loadCard", { card: id }, (reply) => {
      if (!reply.ok) S.cardLoad[id] = "failed";
      else if (!reply.data.card) S.cardLoad[id] = "missing";
      else {
        S.cardLoad[id] = "ready";
        if (!S.cards[id] && !S.deleted.has(id)) addCard(reply.data.card, reply.data.card.column);
      }
      cardShown();
    });
  }
  function ensureComments(id) {
    if (S.comments[id] && S.comments[id].status !== "failed") return;
    S.comments[id] = { status: "loading", items: [] };
    request("loadComments", { card: id }, (reply) => {
      if (!reply.ok) S.comments[id].status = "failed";
      else S.comments[id] = { status: "ready", items: reply.data.comments };
    });
  }
  function cardState(id) {
    if (S.deleted.has(id)) return "Missing";
    if (S.meta.status === "failed" || S.cardLoad[id] === "failed") return "Failed";
    if (S.cards[id]) return metaReady() ? "Ready" : "Loading";
    if (S.cardLoad[id] === "missing" || allColumnsReady()) return "Missing";
    return "Loading";
  }
  // Called when the card place may have become Ready: comments start then.
  function cardShown() {
    const r = S.route;
    if (r.place === "card" && cardState(r.id) === "Ready") ensureComments(r.id);
  }

  // ---------- navigation ----------

  function canonicalize() {
    const r = S.route;
    if (r.place === "board") {
      r.filter = canonicalFilter(r.filter, metaReady() ? S.meta : null);
      S.lastFilter = r.filter;
    }
    if (r.place !== "missing" && formatAddress(r) !== nav.address()) {
      nav.replace(formatAddress(r), nav.state() ?? {});
    }
  }

  // kind: "first" | "step" | "up" | "history" | "direct". See NAV-T1.
  function arrive(kind, prev) {
    S.pendingBack = false;
    S.carry = null;
    S.selection = [];
    S.ui = blankUi();
    if (S.filterTimer != null) clock.clearTimeout(S.filterTimer);
    S.filterTimer = null;
    const address = nav.address();
    S.route = parseAddress(address);
    if (S.route.place === "missing") S.route.raw = address;
    if (nav.state() == null) nav.replace(address, {});
    canonicalize();
    const r = S.route;
    if (r.place === "board") {
      S.filterDraft = r.filter.q;
      ensureMeta();
      ensureColumns();
    } else if (r.place === "card") {
      ensureMeta();
      ensureCard(r.id);
      cardShown();
    }
    if (kind === "first") {
      effects.scroll = "top";
      return;
    }
    const fromCard = r.place === "board" && prev?.place === "card" && (kind === "history" || kind === "up");
    effects.scroll = kind === "history" ? "restore" : "top";
    if (fromCard && isVisible(prev.id)) {
      S.boardFocus = prev.id;
      focus(`card:${prev.id}`);
      effects.scroll = kind === "history" ? "restore+show" : "show";
    } else focus("title");
  }

  function goUp() {
    const prev = S.route;
    if (nav.state()?.fromBoard) {
      S.pendingBack = true;
      nav.back();
      return;
    }
    nav.push(formatAddress({ place: "board", filter: S.lastFilter ?? emptyFilter() }), {});
    arrive("up", prev);
  }

  // ---------- filter ----------

  function countLine() {
    if (!settled()) return "Loading cards…";
    let total = 0;
    let shown = 0;
    for (const c of S.meta.columns) {
      total += orderOf(c.id).length;
      shown += visibleIn(c.id).length;
    }
    return filterActive(boardFilter()) ? `${shown} of ${countText(total, "card")}` : countText(total, "card");
  }
  function applyFilter(next) {
    if (S.filterTimer != null) clock.clearTimeout(S.filterTimer);
    S.filterTimer = null;
    const r = S.route;
    r.filter = canonicalFilter({ ...r.filter, ...next, q: S.filterDraft }, metaReady() ? S.meta : null);
    S.lastFilter = r.filter;
    nav.replace(formatAddress(r), nav.state() ?? {});
    S.carry = null;
    pruneSelection();
    announce(countLine());
  }

  // ---------- moves ----------

  const limitOf = (col) => S.meta.columns.find((c) => c.id === col)?.limit ?? null;
  const isFull = (col) => limitOf(col) != null && orderOf(col).length >= limitOf(col);
  const fullText = (col) => `${columnName(col)} is full (${countText(limitOf(col), "card")}).`;

  function doMove(moves, ctx) {
    const ids = moves.map((m) => m.card);
    const before = positions(ids);
    for (const m of moves) {
      place(m.card, m.column, m.index);
      S.cards[m.card].pending.move += 1;
    }
    request("moveCards", { moves }, (reply) => {
      const failed = [];
      for (const m of moves) {
        if (S.cards[m.card]) S.cards[m.card].pending.move -= 1;
        const ok = reply.ok && reply.data.results.find((x) => x.card === m.card)?.ok;
        if (!ok) failed.push(m.card);
      }
      const live = failed.filter((id) => S.cards[id] && !S.deleted.has(id));
      restore(before.filter((b) => live.includes(b.card)));
      const done = before.filter((b) => !failed.includes(b.card));
      moveOutcome(ctx, moves, before, done, failed);
    });
  }

  function moveOutcome(ctx, moves, before, done, failed) {
    const undo = () => undoMove(done);
    if (ctx.kind === "single") {
      const id = moves[0].card;
      if (failed.length) {
        raise("error", `Couldn't move ${id}. It is back in ${columnName(before[0].column)}.`, {
          label: "Retry",
          run: () => {
            if (!S.cards[id] || S.deleted.has(id)) return;
            if (isFull(moves[0].column)) raise("info", fullText(moves[0].column));
            else doMove(moves, ctx);
          },
        });
      } else raise("info", `Moved ${id} to ${columnName(moves[0].column)}.`, { label: "Undo", run: undo });
    } else if (ctx.kind === "bulk") {
      const t = columnName(ctx.target);
      const of = `${done.length} of ${countText(ctx.total, "card")}`;
      if (failed.length) {
        for (const id of failed) if (isVisible(id) && !S.selection.includes(id)) S.selection.push(id);
        raise("error", `Moved ${of} to ${t}. Couldn't move ${failed.join(", ")}.`, {
          label: "Retry",
          run: () => bulkMoveCards(failed.filter((id) => S.cards[id] && !S.deleted.has(id)), ctx.target),
        });
      } else if (done.length < ctx.total) {
        raise("info", `Moved ${of} to ${t}. ${fullText(ctx.target)}`, { label: "Undo", run: undo });
      } else raise("info", `Moved ${countText(done.length, "card")} to ${t}.`, { label: "Undo", run: undo });
    } else if (failed.length) {
      const what = failed.length === 1 ? failed[0] : countText(failed.length, "card");
      raise("error", `Couldn't undo the move of ${what}.`, {
        label: "Retry",
        run: () => undoMove(ctx.records.filter((r) => failed.includes(r.card))),
      });
    }
  }

  function undoMove(records) {
    const live = records.filter((r) => S.cards[r.card] && !S.deleted.has(r.card));
    if (!live.length) return;
    const sorted = [...live].sort((a, b) => (a.column === b.column ? a.index - b.index : 0));
    doMove(sorted.map((r) => ({ card: r.card, column: r.column, index: r.index })), { kind: "undo", records: live });
    const first = boardOrder(live.map((r) => r.card))[0];
    if (isVisible(first)) {
      S.boardFocus = first;
      focus(`card:${first}`);
    }
  }

  function bulkMoveCards(ids, target) {
    const candidates = boardOrder(ids).filter((id) => S.cards[id].column !== target && !S.cards[id].pending.move);
    if (!candidates.length) return;
    const limit = limitOf(target);
    const room = limit == null ? candidates.length : limit - orderOf(target).length;
    if (room <= 0) {
      raise("info", fullText(target));
      return;
    }
    const movers = candidates.slice(0, room);
    const base = orderOf(target).length;
    S.selection = S.selection.filter((id) => !movers.includes(id));
    doMove(movers.map((card, i) => ({ card, column: target, index: base + i })), {
      kind: "bulk",
      target,
      total: candidates.length,
    });
  }

  // ---------- delete ----------

  function removeCard(id) {
    const pos = positions([id])[0];
    orderOf(pos.column).splice(pos.index, 1);
    S.deleted.add(id);
    S.selection = S.selection.filter((x) => x !== id);
    return pos;
  }
  function sendDelete(id, pos) {
    request("deleteCard", { card: id }, (reply) => {
      if (reply.ok) {
        delete S.cards[id];
        return;
      }
      S.deleted.delete(id);
      orderOf(pos.column).splice(Math.min(pos.index, orderOf(pos.column).length), 0, id);
      raise("error", `Couldn't delete ${id}. It is back in ${columnName(pos.column)}.`, {
        label: "Retry",
        run: () => {
          if (!S.cards[id] || S.deleted.has(id)) return;
          sendDelete(id, removeCard(id));
        },
      });
    });
  }
  // The request is sent when the notice ends, unless it ends by "Undo".
  function doDelete(id) {
    const pos = removeCard(id);
    raise("info", `Deleted ${id}.`, {
      label: "Undo",
      run: () => {
        S.deleted.delete(id);
        orderOf(pos.column).splice(Math.min(pos.index, orderOf(pos.column).length), 0, id);
        if (isVisible(id)) {
          S.boardFocus = id;
          focus(`card:${id}`);
        }
      },
    }, (reason) => reason !== "action" && sendDelete(id, pos));
  }

  // ---------- card saves ----------

  function save(id, field, op, args, onFail) {
    S.cards[id].pending[field] += 1;
    request(op, args, (reply) => {
      if (S.cards[id]) S.cards[id].pending[field] -= 1;
      if (!reply.ok && S.cards[id]) onFail?.();
    });
  }
  function saveTitle(id, title) {
    const card = S.cards[id];
    const old = card.title;
    card.title = title;
    save(id, "title", "saveTitle", { card: id, title }, () => {
      if (card.title === title) card.title = old;
      raise("error", `Couldn't save the title of ${id}.`, {
        label: "Retry",
        run: () => S.cards[id] && !S.deleted.has(id) && !card.pending.title && saveTitle(id, title),
      });
    });
  }
  function setLabels(ids, compute) {
    const changes = [];
    for (const id of ids) {
      const labels = sortLabels(compute(S.cards[id].labels), S.meta.labels);
      S.cards[id].labels = labels;
      S.cards[id].pending.labels += 1;
      changes.push({ card: id, labels });
    }
    return (then) =>
      request("saveLabels", { changes }, () => {
        for (const id of ids) if (S.cards[id]) S.cards[id].pending.labels -= 1;
        then?.();
      });
  }

  // ---------- intents ----------

  const onBoard = () => S.route.place === "board" && metaReady();
  const onCard = () => S.route.place === "card" && cardState(S.route.id) === "Ready";
  const current = () => S.cards[S.route.id];

  const intents = {
    // navigation
    start() {
      arrive("first", null);
    },
    popped() {
      const prev = S.route;
      arrive(nav.state() == null ? "direct" : "history", prev);
    },
    openHeader() {
      if (S.route.place === "board" && nav.address() === "#/") {
        effects.scroll = "top";
        return;
      }
      const prev = S.route;
      nav.push("#/", {});
      arrive("step", prev);
    },
    openCard(id) {
      if (!onBoard() || S.carry || !isVisible(id)) return;
      const prev = S.route;
      nav.push(formatAddress({ place: "card", id }), { fromBoard: true });
      arrive("step", prev);
    },
    goUp() {
      if (S.route.place === "card") goUp();
    },
    goToBoard() {
      const prev = S.route;
      nav.push("#/", {});
      arrive("step", prev);
    },
    retryPlace() {
      if (S.meta.status === "failed") {
        S.meta.status = "none";
        ensureMeta();
      }
      const r = S.route;
      if (r.place === "card" && S.cardLoad[r.id] === "failed") {
        delete S.cardLoad[r.id];
        ensureCard(r.id);
      }
    },
    retryColumn(col) {
      if (onBoard() && S.columns[col]?.status === "failed") loadColumn(col);
    },

    // filter
    filterText(text) {
      if (!onBoard()) return;
      S.filterDraft = text;
      if (S.filterTimer != null) clock.clearTimeout(S.filterTimer);
      S.filterTimer = later(() => applyFilter({}), FILTER_DELAY);
    },
    commitFilter() {
      if (!onBoard()) return;
      applyFilter({});
      let only = null;
      let n = 0;
      for (const c of S.meta.columns) {
        for (const id of visibleIn(c.id)) {
          n += 1;
          only = id;
        }
      }
      if (n === 1) {
        S.boardFocus = only;
        focus(`card:${only}`);
      }
    },
    toggleLabelFilter(label) {
      if (!onBoard()) return;
      const has = S.route.filter.labels.includes(label);
      applyFilter({
        labels: has ? S.route.filter.labels.filter((l) => l !== label) : [...S.route.filter.labels, label],
      });
    },
    toggleWhoFilter(who) {
      if (!onBoard()) return;
      const has = S.route.filter.who.includes(who);
      applyFilter({ who: has ? S.route.filter.who.filter((w) => w !== who) : [...S.route.filter.who, who] });
    },
    clearFilters() {
      if (!onBoard()) return;
      S.filterDraft = "";
      applyFilter({ labels: [], who: [] });
      focus("filter");
    },
    focusFilter() {
      if (onBoard() && !S.carry) focus("filter");
    },

    // board focus
    moveFocus(id, dir) {
      if (!onBoard() || S.carry || !isVisible(id)) return;
      const col = S.cards[id].column;
      const v = visibleIn(col);
      const i = v.indexOf(id);
      let next = null;
      if (dir === "up") next = v[i - 1];
      else if (dir === "down") next = v[i + 1];
      else if (dir === "first") next = v[0];
      else if (dir === "last") next = v[v.length - 1];
      else {
        const cols = S.meta.columns.map((c) => c.id);
        const step = dir === "left" ? -1 : 1;
        for (let k = cols.indexOf(col) + step; k >= 0 && k < cols.length; k += step) {
          const w = visibleIn(cols[k]);
          if (w.length) {
            next = w[Math.min(i, w.length - 1)];
            break;
          }
        }
      }
      if (next && next !== id) {
        S.boardFocus = next;
        focus(`card:${next}`);
      }
    },

    // selection
    toggleSelect(id) {
      if (!onBoard() || S.carry || !isVisible(id)) return;
      S.selection = S.selection.includes(id) ? S.selection.filter((x) => x !== id) : [...S.selection, id];
    },
    selectColumn(col) {
      if (!onBoard() || S.carry) return;
      const v = visibleIn(col);
      if (!v.length) return;
      if (v.every((id) => S.selection.includes(id))) S.selection = S.selection.filter((id) => !v.includes(id));
      else S.selection = [...S.selection, ...v.filter((id) => !S.selection.includes(id))];
    },
    clearSelection() {
      if (!S.selection.length) return;
      S.selection = [];
      focus("title");
    },
    bulkMove(target) {
      if (!onBoard() || S.carry || !S.selection.length) return;
      bulkMoveCards(S.selection, target);
    },
    bulkLabel(label) {
      if (!onBoard() || S.carry || !S.selection.length) return;
      const sel = [...S.selection];
      const q = `"${label}"`;
      if (sel.every((id) => S.cards[id].labels.includes(label))) {
        const send = setLabels(sel, (labels) => labels.filter((l) => l !== label));
        pruneSelection();
        send(() => raise("info", `Removed ${q} from ${countText(sel.length, "card")}.`));
        return;
      }
      const lacking = sel.filter((id) => !S.cards[id].labels.includes(label));
      const can = lacking.filter((id) => S.cards[id].labels.length < LABEL_LIMIT);
      const limitText = `A card can have at most ${LABEL_LIMIT} labels.`;
      if (!can.length) {
        raise("info", limitText);
        return;
      }
      const send = setLabels(can, (labels) => [...labels, label]);
      pruneSelection();
      send(() =>
        raise(
          "info",
          can.length < lacking.length
            ? `Added ${q} to ${can.length} of ${countText(lacking.length, "card")}. ${limitText}`
            : `Added ${q} to ${countText(can.length, "card")}.`,
        )
      );
    },

    // carry: one state for the pointer drag and its keyboard equivalent
    pickUp(id) {
      if (!onBoard() || S.carry || !isVisible(id) || S.cards[id].pending.move) return;
      const col = S.cards[id].column;
      S.carry = { id, from: { col, index: orderOf(col).indexOf(id) }, at: { col, v: visibleIn(col).indexOf(id) } };
      S.boardFocus = id;
    },
    carry(dir) {
      const c = S.carry;
      if (!c) return;
      const here = visibleIn(c.at.col, c.id).length;
      if (dir === "up") c.at.v = Math.max(0, c.at.v - 1);
      else if (dir === "down") c.at.v = Math.min(here, c.at.v + 1);
      else {
        const cols = S.meta.columns.map((x) => x.id);
        const step = dir === "left" ? -1 : 1;
        for (let k = cols.indexOf(c.at.col) + step; k >= 0 && k < cols.length; k += step) {
          if (S.columns[cols[k]].status !== "ready") continue;
          c.at = { col: cols[k], v: Math.min(c.at.v, visibleIn(cols[k], c.id).length) };
          break;
        }
      }
    },
    carryTo(col, v) {
      const c = S.carry;
      if (!c || S.columns[col]?.status !== "ready") return;
      c.at = { col, v: Math.min(Math.max(v, 0), visibleIn(col, c.id).length) };
    },
    drop() {
      const c = S.carry;
      if (!c) return;
      S.carry = null;
      const order = orderOf(c.at.col).filter((id) => id !== c.id);
      const index = dropIndex(order, visibleIn(c.at.col, c.id), c.at.v);
      if (c.at.col === c.from.col && index === c.from.index) return;
      if (c.at.col !== c.from.col && isFull(c.at.col)) {
        raise("info", fullText(c.at.col));
        return;
      }
      doMove([{ card: c.id, column: c.at.col, index }], { kind: "single" });
    },
    cancelCarry() {
      S.carry = null;
    },

    // delete
    deleteCard(id) {
      if (S.route.place === "board") {
        if (!onBoard() || S.carry || !isVisible(id) || S.cards[id].pending.move) return;
        const v = visibleIn(S.cards[id].column);
        const i = v.indexOf(id);
        const next = v[i + 1] ?? v[i - 1] ?? null;
        doDelete(id);
        S.boardFocus = next;
        focus(next ? `card:${next}` : "title");
        return;
      }
      if (!onCard() || S.route.id !== id) return;
      const prev = S.route;
      const fromBoard = nav.state()?.fromBoard;
      doDelete(id);
      if (fromBoard) {
        S.pendingBack = true;
        nav.back();
      } else {
        nav.replace(formatAddress({ place: "board", filter: S.lastFilter ?? emptyFilter() }), {});
        arrive("up", prev);
      }
    },

    // notice
    noticeAction() {
      const n = S.notice;
      if (!n?.action) return;
      endNotice("action");
      n.action.run();
    },
    undo() {
      if (S.notice?.action?.label === "Undo") intents.noticeAction();
    },
    dismissNotice() {
      if (S.notice?.kind === "error") endNotice("dismissed");
    },

    // dismiss: one intent, decided by DIS-T1 (board) and DIS-T2 (card)
    dismiss(where) {
      const r = S.route;
      if (r.place === "board") {
        if (S.carry) S.carry = null;
        else if (where === "filter" && S.filterDraft !== "") {
          S.filterDraft = "";
          applyFilter({});
        } else if (where === "filter") {
          const stop = boardStop();
          focus(stop ? `card:${stop}` : "title");
        } else if (S.selection.length) S.selection = [];
      } else if (r.place === "card") {
        if (where === "title-field") intents.cancelTitle();
        else if (where === "description-field") intents.cancelDescription();
        else if (where !== "comment-field") goUp();
      }
    },

    // card: title
    editTitle() {
      if (!onCard() || S.ui.editTitle || current().pending.title) return;
      S.ui.editTitle = { draft: current().title, message: "" };
      focus("title-field");
    },
    titleText(text) {
      if (S.ui.editTitle) S.ui.editTitle.draft = text;
    },
    commitTitle() {
      const e = S.ui.editTitle;
      if (!onCard() || !e) return;
      const title = squash(e.draft);
      const problem = titleProblem(title);
      if (problem) {
        e.message = problem;
        announce(problem);
        return;
      }
      S.ui.editTitle = null;
      focus("title");
      if (title !== current().title) saveTitle(S.route.id, title);
    },
    // Focus left the field: a good draft is saved, a bad draft is dropped.
    leaveTitle() {
      const e = S.ui.editTitle;
      if (!onCard() || !e) return;
      const title = squash(e.draft);
      S.ui.editTitle = null;
      if (!titleProblem(title) && title !== current().title) saveTitle(S.route.id, title);
    },
    cancelTitle() {
      if (!S.ui.editTitle) return;
      S.ui.editTitle = null;
      focus("title");
    },

    // card: labels and assignee
    toggleLabel(label) {
      if (!onCard()) return;
      const card = current();
      const has = card.labels.includes(label);
      if (!has && card.labels.length >= LABEL_LIMIT) return;
      setLabels([card.id], (labels) => (has ? labels.filter((l) => l !== label) : [...labels, label]))();
    },
    setAssignee(who) {
      if (!onCard() || current().assignee === who) return;
      current().assignee = who;
      save(S.route.id, "assignee", "saveAssignee", { card: S.route.id, assignee: who });
    },

    // card: description
    editDescription() {
      if (!onCard() || S.ui.editDescription || current().pending.description) return;
      S.ui.editDescription = { draft: current().description };
      focus("description-field");
    },
    descriptionText(text) {
      if (S.ui.editDescription) S.ui.editDescription.draft = text;
    },
    commitDescription() {
      const e = S.ui.editDescription;
      if (!onCard() || !e) return;
      const text = e.draft.trim();
      S.ui.editDescription = null;
      focus("edit-description");
      if (text === current().description) return;
      current().description = text;
      save(S.route.id, "description", "saveDescription", { card: S.route.id, description: text });
    },
    cancelDescription() {
      if (!S.ui.editDescription) return;
      S.ui.editDescription = null;
      focus("edit-description");
    },

    // card: comments
    commentText(text) {
      if (!onCard()) return;
      S.ui.commentDraft = text;
      S.ui.commentError = "";
    },
    commitComment() {
      if (!onCard()) return;
      const id = S.route.id;
      const text = S.ui.commentDraft.trim();
      const list = S.comments[id];
      if (!text || S.sending.has(id) || list?.status !== "ready") return;
      const entry = { author: S.meta.currentUser, at: null, text };
      list.items.push(entry);
      S.cards[id].comments += 1;
      S.sending.add(id);
      S.ui.commentDraft = "";
      S.ui.commentError = "";
      request("addComment", { card: id, text }, (reply) => {
        S.sending.delete(id);
        if (reply.ok) {
          entry.at = reply.data.comment.at;
          return;
        }
        list.items.splice(list.items.indexOf(entry), 1);
        if (S.cards[id]) S.cards[id].comments -= 1;
        if (S.route.place === "card" && S.route.id === id) {
          S.ui.commentDraft = text;
          S.ui.commentError = "Couldn't add the comment. Your text is back in the field.";
          announce(S.ui.commentError);
          focus("comment-field");
        } else raise("error", `Couldn't add the comment on ${id}.`);
      });
    },
    retryComments() {
      if (onCard() && S.comments[S.route.id]?.status === "failed") ensureComments(S.route.id);
    },
  };

  // ---------- model ----------

  function noticeModel() {
    const n = S.notice;
    return n ? { kind: n.kind, text: n.text, action: n.action?.label ?? null } : null;
  }

  function boardModel() {
    const f = S.route.filter;
    const m = { place: "board", state: "Loading", title: "Board", notice: noticeModel() };
    if (S.meta.status === "failed") return { ...m, state: "Failed" };
    if (!metaReady()) return m;
    const active = filterActive(f);
    let total = 0;
    let shown = 0;
    const stop = S.carry ? S.carry.id : boardStop();
    const columns = S.meta.columns.map((c) => {
      const col = S.columns[c.id];
      const all = orderOf(c.id).length;
      const ids = visibleIn(c.id, S.carry?.id);
      if (S.carry?.at.col === c.id) ids.splice(S.carry.at.v, 0, S.carry.id);
      const vis = visibleIn(c.id).length;
      total += all;
      shown += vis;
      let state = "Cards";
      if (col.status === "loading" || col.status === "none") state = "Loading";
      else if (col.status === "failed") state = "Failed";
      else if (ids.length === 0) state = all === 0 ? "Empty" : "NoMatch";
      return {
        id: c.id,
        name: c.name,
        limit: c.limit,
        state,
        slow: col.slow,
        count: col.status !== "ready" ? "" : active ? `${vis} of ${countText(all, "card")}` : countText(all, "card"),
        cards: col.status !== "ready" ? [] : ids.map((id) => {
          const card = S.cards[id];
          return {
            id,
            title: card.title,
            labels: card.labels,
            assignee: card.assignee ? personName(card.assignee) : "Unassigned",
            comments: card.comments ? countText(card.comments, "comment") : null,
            pending: card.pending.move > 0,
            selected: S.selection.includes(id),
            carried: S.carry?.id === id,
            stop: stop === id,
          };
        }),
      };
    });
    let line = null;
    if (settled() && total === 0) line = { text: "This board has no cards yet.", button: null };
    else if (settled() && active && shown === 0) {
      line = { text: "No cards match these filters.", button: "Show all cards" };
    }
    const sel = S.selection;
    return {
      ...m,
      state: "Ready",
      carrying: !!S.carry,
      filter: {
        text: S.filterDraft,
        labels: S.meta.labels.map((id) => ({ id, on: f.labels.includes(id) })),
        who: [...S.meta.people, { id: "none", name: "Unassigned" }].map((p) => ({ ...p, on: f.who.includes(p.id) })),
        clear: active || S.filterDraft !== "",
        count: countLine(),
      },
      selection: sel.length
        ? {
          count: `${sel.length} selected`,
          targets: S.meta.columns.map((c) => ({ id: c.id, name: c.name })),
          labels: S.meta.labels.map((id) => {
            const n = sel.filter((x) => S.cards[x].labels.includes(id)).length;
            return { id, state: n === sel.length ? "on" : n === 0 ? "off" : "mixed" };
          }),
        }
        : null,
      columns,
      line,
    };
  }

  function cardModel() {
    const id = S.route.id;
    const state = cardState(id);
    const m = { place: "card", state, id, notice: noticeModel() };
    if (state === "Missing") {
      return {
        place: "missing",
        kind: "card",
        title: "Card not found",
        text: `There is no card ${id} on this board.`,
        link: "Go to the board",
        notice: noticeModel(),
      };
    }
    if (state !== "Ready") return m;
    const card = S.cards[id];
    const list = S.comments[id] ?? { status: "loading", items: [] };
    const full = card.labels.length >= LABEL_LIMIT;
    const cState = { loading: "Loading", failed: "Failed" }[list.status] ?? (list.items.length ? "Some" : "None");
    return {
      ...m,
      column: columnName(card.column),
      title: card.title,
      editTitle: S.ui.editTitle,
      labels: S.meta.labels.map((l) => ({ id: l, on: card.labels.includes(l), off: full && !card.labels.includes(l) })),
      labelNote: full ? `Label limit reached (${LABEL_LIMIT})` : "",
      assignee: [{ id: null, name: "Unassigned" }, ...S.meta.people].map((p) => ({ ...p, on: card.assignee === p.id })),
      description: card.description,
      editDescription: S.ui.editDescription,
      pending: {
        title: card.pending.title > 0,
        labels: card.pending.labels > 0,
        assignee: card.pending.assignee > 0,
        description: card.pending.description > 0,
      },
      comments: {
        state: cState,
        heading: cState === "Some" ? countText(list.items.length, "comment") : "",
        items: list.items.map((c) => ({
          author: personName(c.author),
          time: c.at ? formatTime(c.at) : "Sending…",
          text: c.text,
        })),
        draft: S.ui.commentDraft,
        fieldOff: list.status !== "ready" || S.sending.has(id),
        buttonOff: list.status !== "ready" || S.sending.has(id) || S.ui.commentDraft.trim() === "",
        error: S.ui.commentError,
      },
    };
  }

  function model() {
    const r = S.route;
    if (r.place === "board") return boardModel();
    if (r.place === "card") return cardModel();
    return {
      place: "missing",
      kind: "page",
      title: "Page not found",
      text: "The address may be mistyped or out of date.",
      link: "Go to the board",
      notice: noticeModel(),
    };
  }

  const api = { model, state: S };
  for (const [name, fn] of Object.entries(intents)) api[name] = act(fn);
  api.takeEffects = () => {
    const e = effects;
    effects = { focus: null, scroll: null, announce: [] };
    return e;
  };
  api.holdPaint = () => S.pendingBack;
  return api;
}
