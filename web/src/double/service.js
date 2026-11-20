// Service double. It is driven by fixture/service.json (latency and faults)
// and fixture/data.json (the data set). It holds the session data: a save
// that succeeds changes what a later load returns.

/**
 * @param {{data: object, config: object, profile: string, clock: object}} options
 * @returns {{call: (op: string, args: object, onReply: (reply: object) => void) => void, log: object[]}}
 */
export function createService({ data, config, profile, clock }) {
  const plan = config.profiles[profile];
  if (!plan) throw new Error(`Unknown fixture profile: ${profile}`);
  const full = plan.data === "full";
  const columns = data.columns.map((c) => ({ ...c }));
  const cards = new Map();
  const order = new Map(columns.map((c) => [c.id, []]));
  if (full) {
    for (const c of data.cards) {
      cards.set(c.id, {
        id: c.id,
        title: c.title,
        description: c.description,
        labels: [...c.labels],
        assignee: c.assignee,
        comments: c.comments.map((m) => ({ ...m })),
      });
      order.get(c.column).push(c.id);
    }
  }
  // "skip" is the number of matching replies that pass before the fault is used.
  const faults = plan.faults.map((name) => ({
    name,
    ...config.faults[name],
    left: config.faults[name].times,
    skip: config.faults[name].skip ?? 0,
  }));
  const log = [];

  const columnOf = (id) => {
    for (const [col, ids] of order) if (ids.includes(id)) return col;
    return null;
  };
  const view = (id) => {
    const c = cards.get(id);
    return {
      id: c.id,
      title: c.title,
      description: c.description,
      labels: [...c.labels],
      assignee: c.assignee,
      comments: c.comments.length,
    };
  };
  // Times are written in UTC with whole seconds.
  const iso = (ms) => new Date(Math.floor(ms / 1000) * 1000).toISOString().replace(".000Z", "Z");

  // A fault is used when the reply is made, so each fault is used in reply order.
  function takeFault(op, args, item) {
    for (const f of faults) {
      if (f.op !== op || f.left <= 0) continue;
      let hit = true;
      if (f.item) hit = item != null && Object.entries(f.item).every(([k, v]) => item[k] === v);
      else if (item != null) hit = false;
      if (hit && f.where) hit = Object.entries(f.where).every(([k, v]) => args[k] === v);
      if (hit && f.contains) {
        hit = Object.entries(f.contains).every(([k, v]) => String(args[k] ?? "").toLowerCase().includes(v));
      }
      if (hit && f.skip > 0) {
        f.skip -= 1;
        continue;
      }
      if (hit) {
        f.left -= 1;
        return true;
      }
    }
    return false;
  }

  function latencyOf(op, args) {
    for (const s of config.slow) {
      if (s.op === op && Object.entries(s.where).every(([k, v]) => args[k] === v)) return s.latency;
    }
    return config.latency[op];
  }

  const handlers = {
    loadBoard: () => ({
      columns: columns.map((c) => ({ ...c })),
      people: data.people.map((p) => ({ ...p })),
      labels: [...data.labels],
      currentUser: config.currentUser,
    }),
    loadColumn: ({ column }) => ({ cards: order.get(column).map(view) }),
    loadCard: ({ card }) => {
      if (!cards.has(card)) return { card: null };
      return { card: { ...view(card), column: columnOf(card) } };
    },
    loadComments: ({ card }) => ({ comments: cards.get(card).comments.map((m) => ({ ...m })) }),
    moveCards: (args) => {
      const results = [];
      for (const move of args.moves) {
        if (!cards.has(move.card) || takeFault("moveCards", args, move)) {
          results.push({ card: move.card, ok: false });
          continue;
        }
        const from = order.get(columnOf(move.card));
        from.splice(from.indexOf(move.card), 1);
        const to = order.get(move.column);
        to.splice(Math.min(move.index, to.length), 0, move.card);
        results.push({ card: move.card, ok: true });
      }
      return { results };
    },
    saveTitle: ({ card, title }) => {
      cards.get(card).title = title;
      return {};
    },
    saveDescription: ({ card, description }) => {
      cards.get(card).description = description;
      return {};
    },
    saveLabels: ({ changes }) => {
      for (const ch of changes) cards.get(ch.card).labels = [...ch.labels];
      return {};
    },
    saveAssignee: ({ card, assignee }) => {
      cards.get(card).assignee = assignee;
      return {};
    },
    addComment: ({ card, text }) => {
      const comment = { author: config.currentUser, at: iso(clock.now()), text };
      cards.get(card).comments.push(comment);
      return { comment: { ...comment } };
    },
    deleteCard: ({ card }) => {
      const col = columnOf(card);
      if (col) order.get(col).splice(order.get(col).indexOf(card), 1);
      cards.delete(card);
      return {};
    },
  };

  return {
    log,
    call(op, args, onReply) {
      if (!handlers[op]) throw new Error(`Unknown operation: ${op}`);
      log.push({ op, args: JSON.parse(JSON.stringify(args)), at: clock.now() });
      clock.setTimeout(() => {
        // moveCards uses faults per item; every other operation fails as a whole.
        if (op !== "moveCards" && takeFault(op, args, null)) {
          onReply({ ok: false });
          return;
        }
        onReply({ ok: true, data: handlers[op](args) });
      }, latencyOf(op, args));
    },
  };
}
