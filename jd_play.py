# -*- coding: utf-8 -*-
"""JD Play fetcher: сканирует публичные ATS-борды из open-jobs-data (378 компаний),
вытаскивает компании, нанимающие outbound-роли (SDR/BDR/AE/RevOps/sales leadership).
Выход: jd_leads.json — [{company, ats, role, title, location, url, fetched_at}]
Stdlib only. Polite: 0.25s пауза, UA, таймаут.
"""
import json, time, urllib.request, urllib.error, datetime, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLUGS = os.path.join(HERE, "companies.json")
OUT = os.path.join(HERE, "jd_leads.json")
UA = {"User-Agent": "pipeline-factory-research/1.0"}

# trigger dictionary (scrapewise 2026 + allstonlabs): роли = одобренный бюджет на outbound
KEYS = ["sdr", "bdr", "sales development", "business development rep",
        "account executive", "revops", "revenue operations",
        "head of sales", "vp sales", "vp of sales", "director of sales",
        "sales manager", "appointment setter", "inside sales"]
# ложные срабатывания: не-продажные роли со словом sales
SKIP = ["salesforce engineer", "sales engineer - platform", "ml ", "machine learning"]

ENDPOINTS = {
    "greenhouse": lambda s: f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs",
    "lever": lambda s: f"https://api.lever.co/v0/postings/{s}?mode=json",
    "ashby": lambda s: f"https://api.ashbyhq.com/posting-api/job-board/{s}",
}

def fetch(platform, slug, timeout=12):
    url = ENDPOINTS[platform](slug)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def extract(platform, slug, data):
    """нормализуем разные формы ATS -> единая схема"""
    out = []
    if platform == "greenhouse":
        jobs = data.get("jobs", [])
        for j in jobs:
            out.append({"title": j.get("title") or "", "location": ((j.get("location") or {}).get("name")) or "",
                        "url": j.get("absolute_url") or "", "posted": (j.get("first_published") or "")[:10]})
    elif platform == "lever":
        for j in data if isinstance(data, list) else []:
            cats = j.get("categories") or {}
            out.append({"title": j.get("text") or "", "location": cats.get("location") or "",
                        "url": j.get("hostedUrl") or "", "posted": ""})
            if not out[-1]["posted"] and j.get("createdAt"):
                out[-1]["posted"] = datetime.datetime.utcfromtimestamp(j["createdAt"]/1000).strftime("%Y-%m-%d")
    elif platform == "ashby":
        for j in data.get("jobs", []):
            if j.get("isListed") is False: continue
            out.append({"title": j.get("title") or "", "location": j.get("location") or "",
                        "url": j.get("jobUrl") or j.get("applyUrl") or "", "posted": (j.get("publishedAt") or "")[:10]})
    return out

def match(title):
    t = title.lower()
    if any(s in t for s in SKIP): return False
    return any(k in t for k in KEYS)

def main(limit_slugs=None):
    companies = json.load(open(SLUGS, encoding="utf-8"))
    if limit_slugs: companies = companies[:limit_slugs]
    # только платформы с публичными GET-API из ENDPOINTS; остальные (workday/personio/...) — позже
    hits, scanned, errors = [], 0, 0
    seen_co = set()
    for c in companies:
        p, slug = c.get("platform"), c.get("slug")
        if p not in ENDPOINTS: continue
        try:
            data = fetch(p, slug)
            scanned += 1
            for j in extract(p, slug, data):
                if match(j["title"]):
                    hits.append({"company": c["name"], "ats": p, "role": j["title"],
                                 "location": j["location"], "url": j["url"],
                                 "posted": j["posted"], "fetched_at": datetime.date.today().isoformat()})
                    seen_co.add(c["name"])
        except Exception as e:
            errors += 1
            if errors <= 5: print(f"  ERR {slug}: {type(e).__name__}", file=sys.stderr)
        time.sleep(0.25)
    result = {"scanned_boards": scanned, "errors": errors, "companies_hiring": sorted(seen_co),
              "total_roles": len(hits), "hits": hits}
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"scanned={scanned} errors={errors} roles={len(hits)} companies={len(seen_co)} -> {OUT}")

def _selfcheck():
    """минимальная логика матчинга без сети"""
    assert match("Sales Development Representative")
    assert match("Senior Account Executive, EMEA")
    assert match("VP Sales")
    assert match("RevOps Manager")
    assert not match("Salesforce Engineer")
    assert not match("Machine Learning Engineer")
    assert not match("Senior Backend Engineer")
    # extract: greenhouse-форма
    gh = extract("greenhouse", "x", {"jobs": [{"title": "SDR", "location": {"name": "NYC"}, "absolute_url": "u", "first_published": "2026-09-01T00:00:00Z"}]})
    assert gh == [{"title": "SDR", "location": "NYC", "url": "u", "posted": "2026-09-01"}], gh
    print("jd_play self-check OK")

if __name__ == "__main__":
    if "--selfcheck" in sys.argv: _selfcheck()
    else: main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
