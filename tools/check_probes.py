"""Runs every probe in probes/ through the raw driver and prints the checks that do not hold.

The probe author runs this inside the work directory. It needs no network.
"""
import json
import pathlib
import time

work = pathlib.Path(".")
(work / "requests").mkdir(exist_ok=True)


def column_cards(screen, column):
    lines = screen.split("\n")
    start = next((i for i, l in enumerate(lines) if l.strip().startswith(f'- region "{column}"')), -1)
    if start < 0:
        return None
    depth = len(lines[start]) - len(lines[start].lstrip())
    out = []
    for l in lines[start + 1:]:
        if l.strip() and len(l) - len(l.lstrip()) <= depth:
            break
        if '- group "SL-' in l:
            out.append(l.split('- group "')[1].split(" ")[0])
    return out


def bad_checks(probe, result):
    if not isinstance(result, list) or "error" in result[-1]:
        return [("(run)", result[-1].get("error") if isinstance(result, list) else result)]
    first, last = result[0], result[-1]
    said = [a for r in result for a in r.get("announcements", [])]
    bad = []
    for c in probe.get("checks", []):
        if "focus" in c:
            f = last["focus"]
            ok = f is None if c["focus"] is None else bool(f) and f["role"] == c["focus"]["role"] and f["name"] == c["focus"]["name"]
            saw = f
        elif "address" in c:
            ok, saw = last["address"] == c["address"], last["address"]
        elif "historyDelta" in c:
            saw = last["historyLength"] - first["historyLength"]
            ok = saw == c["historyDelta"]
        elif "windowTitle" in c:
            ok, saw = last["windowTitle"] == c["windowTitle"], last["windowTitle"]
        elif "screenHas" in c:
            ok, saw = c["screenHas"] in last["screen"], "not on the screen"
        elif "screenLacks" in c:
            ok, saw = c["screenLacks"] not in last["screen"], "on the screen"
        elif "requests" in c:
            saw = len([r for r in last["requests"] if r["op"] == c["requests"]["op"]])
            ok = saw == c["requests"]["count"]
        elif "announced" in c:
            ok, saw = c["announced"] in said, said
        elif "order" in c:
            saw = column_cards(last["screen"], c["order"]["column"])
            ok = saw == c["order"]["cards"]
        else:
            ok, saw = False, "unknown check"
        if not ok:
            bad.append((c, saw))
    return bad


failed = 0
files = sorted((work / "probes").glob("PRB-*.json"))
for f in files:
    probe = json.loads(f.read_text())
    stamp = f"{probe['id']}-{int(time.time() * 1000)}"
    (work / "requests" / f"{stamp}.json").write_text(json.dumps(probe["request"]))
    out = work / "results" / f"{stamp}.json"
    for _ in range(200):
        if out.exists():
            break
        time.sleep(0.3)
    if not out.exists():
        print(f"{probe['id']}: no result from the driver")
        failed += 1
        continue
    time.sleep(0.2)
    bad = bad_checks(probe, json.loads(out.read_text()))
    if bad:
        failed += 1
        for check, saw in bad:
            print(f"{probe['id']}: FAILS {json.dumps(check)}  saw: {json.dumps(saw)}")
print(f"{len(files)} probes, {failed} with a check that does not hold")
