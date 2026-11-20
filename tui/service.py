"""Service double (fixture/fixture.md FIX-7 to FIX-19, fixture/service.json).

Each call is logged at once ({op, at}). The reply is made when its latency has
passed on the clock: the faults are looked at and the data is read or changed
at that moment ("A fault is used when the reply is made").
"""
import copy
import json
import os

CARD_KEYS = ("id", "title", "description", "labels", "assignee")


def load_fixture(fixture_dir):
    with open(os.path.join(fixture_dir, "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    with open(os.path.join(fixture_dir, "service.json"), encoding="utf-8") as f:
        service = json.load(f)
    return data, service


class _Fault:
    def __init__(self, name, spec):
        self.name = name
        self.op = spec["op"]
        self.where = spec.get("where")
        self.contains = spec.get("contains")
        self.item = spec.get("item")
        self.skip = int(spec.get("skip", 0))
        self.times = int(spec.get("times", 1))

    def matches_call(self, op, args):
        if op != self.op or self.item is not None:
            return False
        if self.where:
            for k, v in self.where.items():
                if args.get(k) != v:
                    return False
        if self.contains:
            for k, v in self.contains.items():
                if str(v).lower() not in str(args.get(k, "")).lower():
                    return False
        return True

    def matches_item(self, op, item):
        if op != self.op or self.item is None:
            return False
        return all(item.get(k) == v for k, v in self.item.items())

    def use(self):
        """Count one matching occurrence. True if this occurrence fails."""
        if self.times <= 0:
            return False
        if self.skip > 0:
            self.skip -= 1
            return False
        self.times -= 1
        return True


class Service:
    def __init__(self, clock, fixture_dir, profile="default", fixture=None):
        self.clock = clock
        data, cfg = fixture if fixture is not None else load_fixture(fixture_dir)
        if profile not in cfg["profiles"]:
            raise ValueError("unknown profile: %s" % profile)
        prof = cfg["profiles"][profile]
        self.cfg = cfg
        self.latency = dict(cfg["latency"])
        self.slow = list(cfg.get("slow", []))
        self.current_user = cfg.get("currentUser", "mika")
        self.columns = copy.deepcopy(data["columns"])
        self.people = copy.deepcopy(data["people"])
        self.labels = list(data["labels"])
        self.col_cards = {c["id"]: [] for c in self.columns}
        self.cards = {}
        if prof.get("data", "full") == "full":
            for c in data["cards"]:
                card = copy.deepcopy(c)
                self.cards[card["id"]] = card
                self.col_cards[card["column"]].append(card["id"])
        self.faults = [_Fault(n, cfg["faults"][n]) for n in prof.get("faults", [])]
        self.log = []

    # -- calls ------------------------------------------------------------
    def call(self, op, args, callback=None):
        args = copy.deepcopy(args)
        self.log.append({"op": op, "at": self.clock.now})
        delay = self._latency(op, args)

        def reply():
            r = self._reply(op, args)
            if callback is not None:
                callback(r)

        self.clock.schedule(delay, reply)

    def _latency(self, op, args):
        for s in self.slow:
            if s["op"] == op and all(args.get(k) == v for k, v in s.get("where", {}).items()):
                return int(s["latency"])
        return int(self.latency.get(op, 0))

    def _call_fails(self, op, args):
        for f in self.faults:
            if f.matches_call(op, args) and f.times > 0:
                if f.use():
                    return True
        return False

    def _item_fails(self, op, item):
        for f in self.faults:
            if f.matches_item(op, item) and f.times > 0:
                if f.use():
                    return True
        return False

    def _reply(self, op, args):
        if self._call_fails(op, args):
            return {"ok": False}
        fn = getattr(self, "_op_" + op, None)
        if fn is None:
            return {"ok": False}
        return {"ok": True, "data": fn(args)}

    # -- data -------------------------------------------------------------
    def _card_data(self, cid, with_column=False):
        c = self.cards[cid]
        d = {k: copy.deepcopy(c[k]) for k in CARD_KEYS}
        d["comments"] = len(c["comments"])
        if with_column:
            d["column"] = c["column"]
        return d

    def _op_loadBoard(self, args):
        return {
            "columns": copy.deepcopy(self.columns),
            "people": copy.deepcopy(self.people),
            "labels": list(self.labels),
            "currentUser": self.current_user,
        }

    def _op_loadColumn(self, args):
        ids = self.col_cards.get(args.get("column"), [])
        return {"cards": [self._card_data(i) for i in ids]}

    def _op_loadCard(self, args):
        cid = args.get("card")
        if cid not in self.cards:
            return {"card": None}
        return {"card": self._card_data(cid, with_column=True)}

    def _op_loadComments(self, args):
        cid = args.get("card")
        if cid not in self.cards:
            return {"comments": []}
        return {"comments": copy.deepcopy(self.cards[cid]["comments"])}

    def _op_moveCards(self, args):
        results = []
        for m in args.get("moves", []):
            cid = m.get("card")
            col = m.get("column")
            if self._item_fails("moveCards", m) or cid not in self.cards or col not in self.col_cards:
                results.append({"card": cid, "ok": False})
                continue
            card = self.cards[cid]
            self.col_cards[card["column"]].remove(cid)
            lst = self.col_cards[col]
            idx = int(m.get("index", len(lst)))
            if idx < 0 or idx > len(lst):
                idx = len(lst)
            lst.insert(idx, cid)
            card["column"] = col
            results.append({"card": cid, "ok": True})
        return {"results": results}

    def _op_saveTitle(self, args):
        if args.get("card") in self.cards:
            self.cards[args["card"]]["title"] = args.get("title", "")
        return {}

    def _op_saveDescription(self, args):
        if args.get("card") in self.cards:
            self.cards[args["card"]]["description"] = args.get("description", "")
        return {}

    def _op_saveLabels(self, args):
        for ch in args.get("changes", []):
            if ch.get("card") in self.cards:
                self.cards[ch["card"]]["labels"] = list(ch.get("labels", []))
        return {}

    def _op_saveAssignee(self, args):
        if args.get("card") in self.cards:
            self.cards[args["card"]]["assignee"] = args.get("assignee")
        return {}

    def _op_addComment(self, args):
        comment = {"author": self.current_user, "at": self.clock.iso(), "text": args.get("text", "")}
        if args.get("card") in self.cards:
            self.cards[args["card"]]["comments"].append(dict(comment))
        return {"comment": comment}

    def _op_deleteCard(self, args):
        cid = args.get("card")
        if cid in self.cards:
            card = self.cards.pop(cid)
            self.col_cards[card["column"]].remove(cid)
        return {}
