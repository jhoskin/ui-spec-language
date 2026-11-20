"""Service double (fixture/fixture.md FIX-7 to FIX-19).

Each call is logged at call time. Its reply is made after the latency of the
operation; the fault check and the data effect happen when the reply is made
("A fault is used when the reply is made"), so a load returns the data as it is
at its reply time.
"""
import copy
import datetime
import json
import os

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixture")


def load_fixture(fixture_dir=None):
    d = fixture_dir or FIXTURE_DIR
    with open(os.path.join(d, "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    with open(os.path.join(d, "service.json"), encoding="utf-8") as f:
        service = json.load(f)
    return data, service


def iso_at(clock_start, ms):
    start = datetime.datetime.strptime(clock_start, "%Y-%m-%dT%H:%M:%SZ")
    t = start + datetime.timedelta(seconds=ms // 1000)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


class ServiceDouble:
    def __init__(self, clock, profile="default", fixture=None):
        data, service = fixture or load_fixture()
        if profile not in service["profiles"]:
            raise ValueError("unknown profile: %s" % profile)
        self.clock = clock
        self.service = service
        self.profile = profile
        prof = service["profiles"][profile]
        self.current_user = service.get("currentUser")
        self.columns = copy.deepcopy(data["columns"])
        self.people = copy.deepcopy(data["people"])
        self.labels = list(data["labels"])
        self.cards = {}
        self.order = {c["id"]: [] for c in self.columns}
        if prof.get("data", "full") == "full":
            for c in data["cards"]:
                card = copy.deepcopy(c)
                self.cards[card["id"]] = card
                self.order[card["column"]].append(card["id"])
        self.faults = []
        for name in prof.get("faults", []):
            f = copy.deepcopy(service["faults"][name])
            f["name"] = name
            f["left"] = f.get("times", 1)
            f["seen"] = 0
            self.faults.append(f)
        self.log = []  # [{"op", "at"}]

    # ---- calls -------------------------------------------------------------
    def call(self, op, args, callback):
        args = copy.deepcopy(args)
        self.log.append({"op": op, "at": self.clock.now})
        delay = self._latency(op, args)
        self.clock.schedule(delay, lambda: callback(self._reply(op, args)))

    def _latency(self, op, args):
        for s in self.service.get("slow", []):
            if s["op"] == op and all(args.get(k) == v for k, v in s.get("where", {}).items()):
                return s["latency"]
        return self.service["latency"][op]

    # ---- faults ------------------------------------------------------------
    def _matches(self, fault, op, args):
        if fault["op"] != op or fault["left"] <= 0 or "item" in fault:
            return False
        for k, v in fault.get("where", {}).items():
            if args.get(k) != v:
                return False
        for k, v in fault.get("contains", {}).items():
            if str(v).lower() not in str(args.get(k, "")).lower():
                return False
        return True

    def _call_fails(self, op, args):
        for f in self.faults:
            if self._matches(f, op, args):
                if f["seen"] < f.get("skip", 0):
                    f["seen"] += 1
                    continue
                f["left"] -= 1
                return True
        return False

    def _item_fails(self, op, item):
        for f in self.faults:
            if f["op"] != op or "item" not in f or f["left"] <= 0:
                continue
            if all(item.get(k) == v for k, v in f["item"].items()):
                if f["seen"] < f.get("skip", 0):
                    f["seen"] += 1
                    continue
                f["left"] -= 1
                return True
        return False

    # ---- replies -----------------------------------------------------------
    def _card_out(self, cid, with_column=False):
        c = self.cards[cid]
        out = {
            "id": c["id"],
            "title": c["title"],
            "description": c["description"],
            "labels": list(c["labels"]),
            "assignee": c["assignee"],
            "comments": len(c["comments"]),
        }
        if with_column:
            out["column"] = c["column"]
        return out

    def _reply(self, op, args):
        if self._call_fails(op, args):
            return {"ok": False}
        fn = getattr(self, "_op_" + op)
        try:
            data = fn(args)
        except KeyError:
            return {"ok": False}
        if data is None:
            return {"ok": False}
        return {"ok": True, "data": data}

    def _op_loadBoard(self, args):
        return {
            "columns": copy.deepcopy(self.columns),
            "people": copy.deepcopy(self.people),
            "labels": list(self.labels),
            "currentUser": self.current_user,
        }

    def _op_loadColumn(self, args):
        col = args["column"]
        if col not in self.order:
            return None
        return {"cards": [self._card_out(cid) for cid in self.order[col]]}

    def _op_loadCard(self, args):
        cid = args["card"]
        if cid not in self.cards:
            return {"card": None}
        return {"card": self._card_out(cid, True)}

    def _op_loadComments(self, args):
        cid = args["card"]
        if cid not in self.cards:
            return None
        return {"comments": copy.deepcopy(self.cards[cid]["comments"])}

    def _op_moveCards(self, args):
        results = []
        for m in args["moves"]:
            cid, col = m["card"], m["column"]
            if cid not in self.cards or col not in self.order or self._item_fails("moveCards", m):
                results.append({"card": cid, "ok": False})
                continue
            card = self.cards[cid]
            self.order[card["column"]].remove(cid)
            target = self.order[col]
            idx = max(0, int(m.get("index", len(target))))
            target.insert(min(idx, len(target)), cid)
            card["column"] = col
            results.append({"card": cid, "ok": True})
        return {"results": results}

    def _op_saveTitle(self, args):
        self.cards[args["card"]]["title"] = args["title"]
        return {}

    def _op_saveDescription(self, args):
        self.cards[args["card"]]["description"] = args["description"]
        return {}

    def _op_saveLabels(self, args):
        for ch in args["changes"]:
            if ch["card"] not in self.cards:
                return None
        for ch in args["changes"]:
            self.cards[ch["card"]]["labels"] = list(ch["labels"])
        return {}

    def _op_saveAssignee(self, args):
        self.cards[args["card"]]["assignee"] = args["assignee"]
        return {}

    def _op_addComment(self, args):
        card = self.cards[args["card"]]
        comment = {
            "author": self.current_user,
            "at": iso_at(self.service["clockStart"], self.clock.now),
            "text": args["text"],
        }
        card["comments"].append(comment)
        return {"comment": copy.deepcopy(comment)}

    def _op_deleteCard(self, args):
        cid = args["card"]
        card = self.cards.pop(cid)
        self.order[card["column"]].remove(cid)
        return {}
