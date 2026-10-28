"""Deterministic scoring + ranking. Standard library only. No AI is used here.

Usage:
    python prototype/score.py                       # prints a table
    python prototype/score.py --out ranking.json    # writes ranking.json
Input: criteria.json (admin-defined) + extracted_facts.json (validated facts).
"""
import argparse, json, os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


def mandatory_check(f):
    """Return (failures -> ineligible, unclear -> flagged)."""
    fails, unclear = [], []
    lic = f.get("licence_held_by_bidder")
    if lic is False:
        fails.append("bidder does not hold the Ontario electrical licence itself")
    elif lic is None:
        unclear.append("licence status unclear")
    for key, label in (("wsib_confirmed", "WSIB clearance"), ("insurance_5m_confirmed", "$5M liability insurance")):
        v = f.get(key)
        if v is False:
            fails.append(f"{label} not confirmed")
        elif v is None:
            unclear.append(f"{label} unclear")
    return fails, unclear


def clamp(x):
    return max(0.0, min(100.0, x))


def run():
    crit, facts = load("criteria.json"), load("extracted_facts.json")
    facts = {k: v for k, v in facts.items() if not k.startswith("_")}
    p = crit["project"]
    weights = {c["id"]: c["weight"] for c in crit["weighted"]}
    assert sum(weights.values()) == 100, "weights must total 100"

    result = {}
    # 1. eligibility and flags
    for k, f in facts.items():
        r = {"status": "ranked", "notes": [], "sub": {}}
        fails, unclear = mandatory_check(f)
        if f.get("price_cad") is not None and f["price_cad"] > p["budget_ceiling_cad"]:
            fails.append("price above budget ceiling")
        if f.get("weeks") is not None and f["weeks"] > p["max_weeks"]:
            fails.append("schedule longer than allowed")
        if fails:
            r["status"], r["notes"] = "ineligible", fails
        else:
            if unclear:
                r["status"] = "flagged"; r["notes"] += unclear
            if f.get("weeks") is None:
                r["status"] = "flagged"; r["notes"].append("completion time not stated")
            if f.get("instruction_like_text"):
                r["status"] = "flagged"; r["notes"].append("instruction-like text aimed at automated reviewers (ignored)")
            if f.get("installs_window_uncertain"):
                r["notes"].append("experience window uncertain")
        result[k] = r

    # 2. sub-scores (0-100) for every non-ineligible proposal
    pool = [k for k, r in result.items() if r["status"] != "ineligible"]
    prices = [facts[k]["price_cad"] for k in pool if facts[k].get("price_cad") is not None]
    weeks = [facts[k]["weeks"] for k in pool if facts[k].get("weeks") is not None]
    lo_price, lo_weeks = (min(prices) if prices else None), (min(weeks) if weeks else None)

    for k in pool:
        f, s = facts[k], result[k]["sub"]
        s["experience"] = clamp(100 * (f.get("installs_100kw_plus_5y") or 0) / p["experience_full_marks_at"])
        if f.get("price_cad") is None:
            s["price"] = 0.0
        elif lo_price == p["budget_ceiling_cad"]:
            s["price"] = 100.0
        else:
            s["price"] = clamp(100 * (p["budget_ceiling_cad"] - f["price_cad"]) / (p["budget_ceiling_cad"] - lo_price))
        if f.get("weeks") is None:
            s["timeline"] = 0.0
        elif lo_weeks == p["max_weeks"]:
            s["timeline"] = 100.0
        else:
            s["timeline"] = clamp(100 * (p["max_weeks"] - f["weeks"]) / (p["max_weeks"] - lo_weeks))
        s["warranty"] = (clamp(100 * (f.get("panel_warranty_years") or 0) / 25) +
                         clamp(100 * (f.get("workmanship_warranty_years") or 0) / 12)) / 2
        s["team"] = 25.0 * sum(bool(f.get(x)) for x in ("named_lead", "crew_stated", "safety_plan", "monitoring_plan"))
        result[k]["score"] = round(sum(s[c] * weights[c] / 100 for c in weights), 1)

    # 3. rank only clean (unflagged) proposals
    ranked = sorted([k for k in pool if result[k]["status"] == "ranked"], key=lambda k: (-result[k]["score"], k))
    for i, k in enumerate(ranked, 1):
        result[k]["rank"] = i
    return result


def reason(k, r):
    if r["status"] == "ineligible":
        return "Fails a mandatory or limit check: " + "; ".join(r["notes"]) + "."
    sub = sorted(r["sub"].items(), key=lambda kv: -kv[1])
    base = f"Strongest on {sub[0][0]}, weakest on {sub[-1][0]}."
    if r["status"] == "flagged":
        return f"Human review needed ({'; '.join(r['notes'])}); provisional score {r['score']}. {base}"
    return base


def to_ranking(result):
    out = []
    for k, r in result.items():
        out.append({"proposal": k, "rank": r.get("rank"), "status": r["status"],
                    "score": r.get("score"), "reason": reason(k, r)})
    order = {"ranked": 0, "flagged": 1, "ineligible": 2}
    out.sort(key=lambda x: (order[x["status"]], x["rank"] or 0, -(x["score"] or 0)))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args()
    res = run()
    for k in sorted(res):
        r = res[k]
        print(k, r["status"], r.get("rank"), r.get("score"), {c: round(v, 1) for c, v in r["sub"].items()}, r["notes"])
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(to_ranking(res), f, indent=2); f.write("\n")
        print("wrote", a.out)
