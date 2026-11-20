// The page layer. It paints `app.model()` and turns keys and pointer events into intents.
// It makes no decision that a user can see, except the focus fallback (FOC-1).

/** Build a virtual node. `props.on` holds event handlers; `props.key` keeps identity. */
function h(tag, props, ...children) {
  return { tag, props: props ?? {}, children: children.flat(Infinity).filter((c) => c != null && c !== false) };
}

const PROPS = new Set(["value", "checked", "disabled"]);

function update(el, v) {
  const next = v.props;
  for (const a of [...el.attributes]) {
    if (!(a.name in next) || next[a.name] == null || next[a.name] === false) el.removeAttribute(a.name);
  }
  for (const [k, val] of Object.entries(next)) {
    if (k === "key" || k === "on") continue;
    if (PROPS.has(k)) {
      if (el[k] !== val) el[k] = val;
    } else if (val != null && val !== false) {
      const s = val === true ? "" : String(val);
      if (el.getAttribute(k) !== s) el.setAttribute(k, s);
    }
  }
  for (const name of el.__events ?? []) el[`on${name}`] = null;
  el.__events = Object.keys(next.on ?? {});
  for (const [name, fn] of Object.entries(next.on ?? {})) el[`on${name}`] = fn;
  patch(el, v.children);
}

function patch(parent, vnodes) {
  const doc = parent.ownerDocument;
  const old = [...parent.childNodes];
  const used = new Set();
  let i = 0;
  for (const raw of vnodes.flat(Infinity).filter((c) => c != null && c !== false)) {
    const v = typeof raw === "object" ? raw : { tag: "#text", text: String(raw), props: {} };
    const key = v.props.key ?? null;
    let node = old.find((n) => !used.has(n) && n.__tag === v.tag && (n.__key ?? null) === key);
    if (!node) {
      node = v.tag === "#text" ? doc.createTextNode("") : doc.createElement(v.tag);
      node.__tag = v.tag;
      node.__key = key;
    }
    used.add(node);
    if (v.tag === "#text") {
      if (node.data !== v.text) node.data = v.text;
    } else update(node, v);
    if (parent.childNodes[i] !== node) parent.insertBefore(node, parent.childNodes[i] ?? null);
    i += 1;
  }
  for (const n of old) if (!used.has(n)) n.remove();
}

export function createView(app, doc) {
  const main = doc.getElementById("main");
  const noticeBox = doc.getElementById("notice");
  const win = doc.defaultView;
  const announcements = [];
  let drag = null;
  let suppressClick = false;

  const press = (fn) => ({ click: (e) => (e.preventDefault(), fn()) });
  const toggle = (name, on, fn, extra) =>
    h("button", { type: "button", "aria-pressed": String(on), on: press(fn), ...extra }, name);

  function boardView(m) {
    const out = [h("h1", { tabindex: "-1", "data-fk": "title" }, m.title)];
    if (m.state === "Loading") {
      out.push(
        h("div", { class: "columns", "aria-busy": "true" }, [0, 1, 2].map(() => h("div", { class: "column ghost" }))),
      );
      return out;
    }
    if (m.state === "Failed") {
      out.push(h("p", { role: "alert" }, "Couldn't load the board."));
      out.push(h("button", { type: "button", on: press(() => app.retryPlace()) }, "Try again"));
      return out;
    }
    const f = m.filter;
    out.push(
      h(
        "section",
        { class: "filters", "aria-label": "Filters" },
        h("input", {
          type: "search",
          "aria-label": "Filter cards",
          placeholder: "Filter cards (press /)",
          "data-fk": "filter",
          value: f.text,
          on: { input: (e) => app.filterText(e.target.value) },
        }),
        h(
          "div",
          { role: "group", "aria-label": "Labels" },
          f.labels.map((l) => toggle(l.id, l.on, () => app.toggleLabelFilter(l.id))),
        ),
        h(
          "div",
          { role: "group", "aria-label": "Assignee" },
          f.who.map((p) => toggle(p.name, p.on, () => app.toggleWhoFilter(p.id))),
        ),
        f.clear && h("button", { type: "button", on: press(() => app.clearFilters()) }, "Clear filters"),
        h("p", { class: "quiet", role: "status" }, f.count),
      ),
    );
    if (m.selection) {
      const s = m.selection;
      out.push(
        h(
          "section",
          { class: "bulk", "aria-label": "Selection" },
          h("p", null, s.count),
          h(
            "div",
            { role: "group", "aria-label": "Move selected to" },
            s.targets.map((t) => h("button", { type: "button", on: press(() => app.bulkMove(t.id)) }, t.name)),
          ),
          h(
            "div",
            { role: "group", "aria-label": "Label selected" },
            s.labels.map((l) =>
              h("button", {
                type: "button",
                "aria-pressed": l.state === "on" ? "true" : l.state === "mixed" ? "mixed" : "false",
                on: press(() => app.bulkLabel(l.id)),
              }, l.id)
            ),
          ),
          h("button", { type: "button", on: press(() => app.clearSelection()) }, "Clear selection"),
        ),
      );
    }
    out.push(h("div", { class: "columns" }, m.columns.map(columnView)));
    if (m.line) {
      out.push(
        h("p", { class: "board-line" }, m.line.text),
        m.line.button && h("button", { type: "button", on: press(() => app.clearFilters()) }, m.line.button),
      );
    }
    return out;
  }

  function columnView(c) {
    let body;
    if (c.state === "Loading") {
      body = [
        h("ul", { "aria-hidden": "true" }, [0, 1, 2].map(() => h("li", { class: "card ghost" }))),
        c.slow && h("p", { class: "quiet" }, "Still loading…"),
      ];
    } else if (c.state === "Failed") {
      body = [
        h("p", { role: "alert" }, `Couldn't load ${c.name}.`),
        h(
          "button",
          { type: "button", "aria-label": `Retry ${c.name}`, on: press(() => app.retryColumn(c.id)) },
          "Retry",
        ),
      ];
    } else if (c.state === "Empty") body = [h("p", { class: "quiet" }, "No cards")];
    else if (c.state === "NoMatch") body = [h("p", { class: "quiet" }, "No matching cards")];
    else body = [h("ul", { class: "cards" }, c.cards.map(cardItem))];
    return h(
      "section",
      {
        class: "column",
        "aria-label": c.name,
        "data-column": c.id,
        key: c.id,
        "aria-busy": c.state === "Loading" ? "true" : null,
      },
      h("h2", null, c.name),
      c.count && h("p", { class: "quiet count" }, c.count),
      c.limit != null && h("p", { class: "quiet" }, `Limit ${c.limit}`),
      c.state === "Cards" &&
        h("button", {
          type: "button",
          class: "small",
          "aria-label": `Select all in ${c.name}`,
          on: press(() => app.selectColumn(c.id)),
        }, "Select all"),
      body,
    );
  }

  function cardItem(c) {
    return h(
      "li",
      { key: c.id },
      h(
        "div",
        {
          class: `card${c.carried ? " carried" : ""}${c.selected ? " selected" : ""}${c.pending ? " pending" : ""}`,
          role: "group",
          "aria-label": `${c.id} ${c.title}`,
          tabindex: c.stop ? "0" : "-1",
          "data-fk": `card:${c.id}`,
          "data-card": c.id,
        },
        h("input", {
          type: "checkbox",
          tabindex: "-1",
          "aria-label": `Select ${c.id}`,
          checked: c.selected,
          on: { click: (e) => (e.preventDefault(), e.target.closest("[data-card]").focus(), app.toggleSelect(c.id)) },
        }),
        h("span", { class: "quiet id" }, c.id),
        h(
          "a",
          { href: `#/card/${c.id}`, tabindex: "-1", class: "title", on: { click: (e) => openFromLink(e, c.id) } },
          c.title,
        ),
        c.labels.length > 0 &&
          h("ul", { class: "labels", "aria-label": "Labels" }, c.labels.map((l) => h("li", null, l))),
        h("span", { class: "quiet who" }, c.assignee),
        c.comments && h("span", { class: "quiet" }, c.comments),
        c.carried && h("span", { class: "mark" }, "Moving"),
        c.pending && h("span", { class: "mark" }, "Saving…"),
      ),
    );
  }

  function openFromLink(e, id) {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1) return; // platform default: new tab
    e.preventDefault();
    if (suppressClick) return;
    app.openCard(id);
  }

  function cardView(m) {
    const up = h("a", { href: "#/", class: "up", on: press(() => app.goUp()) }, "← Board");
    if (m.state === "Loading") {
      return [up, h("div", { class: "ghost block", "aria-busy": "true" }), h("div", { class: "ghost block" })];
    }
    if (m.state === "Failed") {
      return [
        up,
        h("h1", { tabindex: "-1", "data-fk": "title" }, m.id),
        h("p", { role: "alert" }, "Couldn't load this card."),
        h("button", { type: "button", on: press(() => app.retryPlace()) }, "Try again"),
      ];
    }
    const saving = (on) => on && h("span", { class: "mark" }, "Saving…");
    const c = m.comments;
    return [
      up,
      h("p", { class: "quiet" }, `${m.id} · ${m.column}`),
      m.editTitle
        ? [
          h("input", {
            type: "text",
            "aria-label": "Title",
            "data-fk": "title-field",
            class: "title-field",
            value: m.editTitle.draft,
            on: { input: (e) => app.titleText(e.target.value), blur: () => app.leaveTitle() },
          }),
          m.editTitle.message && h("p", { class: "danger", role: "alert" }, m.editTitle.message),
        ]
        : h(
          "div",
          { class: "title-row" },
          h("h1", { tabindex: "-1", "data-fk": "title" }, m.title),
          h("button", { type: "button", "data-fk": "edit-title", on: press(() => app.editTitle()) }, "Edit title"),
          saving(m.pending.title),
        ),
      h(
        "div",
        { role: "group", "aria-label": "Labels", class: "row" },
        m.labels.map((l) => toggle(l.id, l.on, () => app.toggleLabel(l.id), { disabled: l.off })),
        saving(m.pending.labels),
      ),
      m.labelNote && h("p", { class: "quiet" }, m.labelNote),
      h(
        "div",
        { role: "radiogroup", "aria-label": "Assignee", class: "row" },
        m.assignee.map((p) =>
          h("button", {
            type: "button",
            role: "radio",
            "aria-checked": String(p.on),
            on: press(() => app.setAssignee(p.id)),
          }, p.name)
        ),
        saving(m.pending.assignee),
      ),
      h("h2", null, "Description"),
      m.editDescription
        ? [
          h("textarea", {
            "aria-label": "Description",
            "data-fk": "description-field",
            rows: "5",
            value: m.editDescription.draft,
            on: { input: (e) => app.descriptionText(e.target.value) },
          }),
          h(
            "div",
            { class: "row" },
            h("button", { type: "button", on: press(() => app.commitDescription()) }, "Save"),
            h("button", { type: "button", on: press(() => app.cancelDescription()) }, "Cancel"),
          ),
        ]
        : [
          h("p", { class: m.description ? "text" : "quiet" }, m.description || "No description"),
          h(
            "div",
            { class: "row" },
            h(
              "button",
              { type: "button", "data-fk": "edit-description", on: press(() => app.editDescription()) },
              "Edit description",
            ),
            saving(m.pending.description),
          ),
        ],
      h("h2", null, "Comments"),
      c.state === "Loading" && h("div", { class: "ghost block", "aria-busy": "true" }),
      c.state === "Failed" && [
        h("p", { role: "alert" }, "Couldn't load comments."),
        h("button", { type: "button", on: press(() => app.retryComments()) }, "Retry"),
      ],
      c.state === "None" && h("p", { class: "quiet" }, "No comments yet"),
      c.state === "Some" && [
        h("p", { class: "quiet" }, c.heading),
        h(
          "ol",
          { class: "comments" },
          c.items.map((x) =>
            h("li", null, h("p", { class: "quiet" }, `${x.author} · ${x.time}`), h("p", { class: "text" }, x.text))
          ),
        ),
      ],
      h("textarea", {
        "aria-label": "Add a comment",
        placeholder: "Add a comment",
        "data-fk": "comment-field",
        rows: "3",
        disabled: c.fieldOff,
        value: c.draft,
        on: { input: (e) => app.commentText(e.target.value) },
      }),
      h("button", { type: "button", disabled: c.buttonOff, on: press(() => app.commitComment()) }, "Add comment"),
      c.error && h("p", { class: "danger", role: "alert" }, c.error),
      h("hr"),
      h("button", { type: "button", class: "danger-button", on: press(() => app.deleteCard(m.id)) }, "Delete card"),
    ];
  }

  function missingView(m) {
    return [
      h("h1", { tabindex: "-1", "data-fk": "title" }, m.title),
      h("p", { class: "quiet" }, m.text),
      h("a", { href: "#/", on: press(() => app.goToBoard()) }, m.link),
    ];
  }

  function noticeView(n) {
    if (!n) return [];
    return [
      h(
        "div",
        { class: `notice ${n.kind}`, role: n.kind === "error" ? "alert" : "status", "aria-label": "Notice" },
        h("span", null, n.text),
        n.action && h("button", { type: "button", on: press(() => app.noticeAction()) }, n.action),
        n.kind === "error" && h("button", { type: "button", on: press(() => app.dismissNotice()) }, "Dismiss"),
      ),
    ];
  }

  function paint() {
    if (app.holdPaint()) return;
    const m = app.model();
    const before = doc.activeElement;
    const hadFocus = before && before !== doc.body;
    const key = hadFocus ? before.getAttribute("data-fk") : null;
    main.className = `place-${m.place}`;
    patch(main, m.place === "board" ? boardView(m) : m.place === "card" ? cardView(m) : missingView(m));
    patch(noticeBox, noticeView(m.notice));
    doc.title = m.place === "board"
      ? "Slate"
      : m.place === "card" && m.title
      ? `${m.id} ${m.title} · Slate`
      : m.place === "card"
      ? `${m.id} · Slate`
      : "Not found · Slate";

    const e = app.takeEffects();
    for (const text of e.announce) announcements.push(text);
    const find = (k) => doc.querySelector(`[data-fk="${k}"]`);
    if (e.focus === "none") doc.activeElement?.blur?.();
    else if (e.focus) {
      const el = find(e.focus);
      el?.focus();
      if (e.focus === "title-field") el?.select();
    } else if (hadFocus && !before.isConnected || (hadFocus && doc.activeElement === doc.body)) {
      // FOC-1: the part that had focus is gone. The same part, if it is shown again, else the title.
      (key && find(key) || find("title"))?.focus();
    }
    if (e.scroll === "top") win.scrollTo(0, 0);
    else if (e.scroll?.startsWith("restore")) win.scrollTo(...(win.history.state?.scroll ?? [0, 0]));
    if (e.scroll?.endsWith("show")) doc.activeElement?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
  }

  // ---------- keys ----------

  const inText = (el) => el && (el.tagName === "TEXTAREA" || (el.tagName === "INPUT" && el.type !== "checkbox"));

  doc.addEventListener("keydown", (e) => {
    const el = doc.activeElement;
    const fk = el?.getAttribute?.("data-fk") ?? "";
    const m = app.model();
    const mod = e.ctrlKey || e.metaKey;
    const done = () => e.preventDefault();

    if (e.key === "Escape") {
      app.dismiss(fk === "filter" ? "filter" : fk.endsWith("-field") ? fk : "other");
      return done();
    }
    if (fk === "filter") {
      if (e.key === "Enter") done(app.commitFilter());
      return;
    }
    if (fk === "title-field") {
      if (e.key === "Enter") done(app.commitTitle());
      return;
    }
    if (fk === "description-field") {
      if (e.key === "Enter" && mod) done(app.commitDescription());
      return;
    }
    if (fk === "comment-field") {
      if (e.key === "Enter" && mod) done(app.commitComment());
      return;
    }
    if (inText(el)) return;
    if (mod && e.key.toLowerCase() === "z") {
      app.undo();
      return done();
    }
    if (mod || e.altKey) return;
    if (m.place === "board" && e.key === "/") {
      app.focusFilter();
      return done();
    }
    const id = el?.getAttribute?.("data-card");
    if (m.place !== "board" || !id) return;
    const arrows = { ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right" };
    if (m.carrying) {
      if (arrows[e.key]) app.carry(arrows[e.key]);
      else if (e.key === " " || e.key === "Enter") app.drop();
      else return;
      return done();
    }
    if (arrows[e.key]) app.moveFocus(id, arrows[e.key]);
    else if (e.key === "Home") app.moveFocus(id, "first");
    else if (e.key === "End") app.moveFocus(id, "last");
    else if (e.key === "Enter") app.openCard(id);
    else if (e.key === " ") app.pickUp(id);
    else if (e.key === "X") app.selectColumn(el.closest("[data-column]").getAttribute("data-column"));
    else if (e.key === "x") app.toggleSelect(id);
    else if (e.key === "Delete" || e.key === "Backspace") app.deleteCard(id);
    else return;
    done();
  });

  // ---------- pointer drag ----------

  doc.addEventListener("pointerdown", (e) => {
    const card = e.target.closest?.("[data-card]");
    if (!card || e.button !== 0 || e.target.closest("input")) return;
    drag = { id: card.getAttribute("data-card"), x: e.clientX, y: e.clientY, on: false };
  });
  doc.addEventListener("pointermove", (e) => {
    if (!drag) return;
    if (!drag.on) {
      if (Math.hypot(e.clientX - drag.x, e.clientY - drag.y) < 4) return;
      app.pickUp(drag.id);
      if (!app.model().carrying) {
        drag = null;
        return;
      }
      drag.on = true;
    }
    const col = doc.elementFromPoint(e.clientX, e.clientY)?.closest?.("[data-column]");
    if (!col) return;
    let v = 0;
    for (const item of col.querySelectorAll("[data-card]")) {
      if (item.getAttribute("data-card") === drag.id) continue;
      const box = item.getBoundingClientRect();
      if (box.top + box.height / 2 < e.clientY) v += 1;
    }
    app.carryTo(col.getAttribute("data-column"), v);
  });
  doc.addEventListener("pointerup", (e) => {
    if (!drag) return;
    const was = drag;
    drag = null;
    if (!was.on) return;
    suppressClick = true;
    win.setTimeout(() => (suppressClick = false), 0);
    if (doc.elementFromPoint(e.clientX, e.clientY)?.closest?.("[data-column]")) app.drop();
    else app.cancelCarry();
  });
  doc.addEventListener("pointercancel", () => {
    if (drag?.on) app.cancelCarry();
    drag = null;
  });
  // A drag selects no text.
  doc.addEventListener("selectstart", (e) => drag && e.preventDefault());

  doc.addEventListener("focusin", (e) => {
    const id = e.target.getAttribute?.("data-card");
    if (id && !app.model().carrying && !e.target.matches('[tabindex="0"]')) app.noteFocus(id);
  });

  doc.getElementById("home").addEventListener("click", (e) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault();
    app.openHeader();
  });

  win.addEventListener("scroll", () => {
    if (app.holdPaint()) return;
    win.history.replaceState({ ...win.history.state, scroll: [win.scrollX, win.scrollY] }, "");
  });

  return { paint, announcements };
}
