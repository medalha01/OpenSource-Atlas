#!/usr/bin/env python3
"""Validate data/projects.yaml and (optionally) check every link is live.

Usage:
    python tools/check.py            # schema + structure + README freshness (offline, fast)
    python tools/check.py --links    # also HTTP-check every URL (slow, used in scheduled CI)
    python tools/check.py --links --sample 50   # check a random sample of links

Exit code is non-zero if any check fails, so it works as a CI gate and a git hook.
"""
import argparse, concurrent.futures as cf, io, random, re, sys, urllib.request, urllib.error, pathlib
try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import generate  # taxonomy + renderer live here

DATA = ROOT / "data" / "projects.yaml"
README = ROOT / "README.md"
REQUIRED = {"name", "url", "desc", "cat", "sub"}
OPTIONAL = {"alt", "status"}
ALLOWED = REQUIRED | OPTIONAL
VALID_STATUS = {"inactive", "archived", "beta", "deprecated"}
SUBS = {c: subs for c, _, _, subs in generate.TAXONOMY}

# Intentional shared upstream repositories. Multiple independently useful components in
# these projects are listed separately in the atlas, so sharing the canonical monorepo URL
# is expected and should not create validation noise.
ALLOWED_SHARED_URLS = {
    "githubcomapachekafka",
    "githubcomapachehadoop",
    "githubcomapachearrow",
    "githubcomapachespark",
    "githubcomapachehive",
}

def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())

def load():
    docs = list(yaml.safe_load_all(DATA.read_text(encoding="utf-8")))
    if len(docs) != 1 or not isinstance(docs[0], list):
        raise ValueError("data/projects.yaml must contain exactly one top-level YAML list")
    return docs[0]

def validate_schema(rows):
    errs, warns = [], []
    seen_urls, seen_names = {}, {}
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            errs.append(f"entry #{i+1}: expected a mapping/object, got {type(r).__name__}")
            continue
        where = f"entry #{i+1} ({r.get('name','<no name>')!r})"
        keys = set(r)
        for k in REQUIRED - keys:
            errs.append(f"{where}: missing required field '{k}'")
        for k in keys - ALLOWED:
            errs.append(f"{where}: unknown field '{k}'")
        if not REQUIRED <= keys:
            continue
        for field in REQUIRED:
            if not isinstance(r[field], str) or not r[field].strip():
                errs.append(f"{where}: field '{field}' must be a non-empty string")
        if any(not isinstance(r[field], str) or not r[field].strip() for field in REQUIRED):
            continue
        alt = r.get("alt", []) or []
        status = r.get("status", []) or []
        if not isinstance(alt, list) or any(not isinstance(u, str) or not u.strip() for u in alt):
            errs.append(f"{where}: alt must be a list of non-empty URL strings")
            alt = []
        if not isinstance(status, list) or any(not isinstance(st, str) or not st.strip() for st in status):
            errs.append(f"{where}: status must be a list of non-empty strings")
            status = []
        if not re.match(r"^https://", r["url"]):
            errs.append(f"{where}: url must start with https:// ({r['url']})")
        if r["desc"].endswith("."):
            warns.append(f"{where}: description ends with a period (style: drop it)")
        if len(r["desc"]) > 120:
            warns.append(f"{where}: description is long ({len(r['desc'])} chars)")
        if r["cat"] not in SUBS:
            errs.append(f"{where}: unknown category {r['cat']!r}")
        elif r["sub"] not in SUBS[r["cat"]]:
            errs.append(f"{where}: subcategory {r['sub']!r} not valid for category {r['cat']!r}")
        for st in status:
            if st.lower() not in VALID_STATUS:
                warns.append(f"{where}: unusual status {st!r} (known: {', '.join(sorted(VALID_STATUS))})")
        for u in [r["url"]] + alt:
            if not re.match(r"^https://", u):
                errs.append(f"{where}: alternate URL must start with https:// ({u})")
                continue
            key = norm(re.sub(r"^https?://(www\.)?", "", u).rstrip("/"))
            if key in seen_urls and seen_urls[key] != r["name"] and key not in ALLOWED_SHARED_URLS:
                warns.append(f"{where}: url {u} also used by {seen_urls[key]!r}")
            seen_urls[key] = r["name"]
        nk = norm(r["name"])
        if nk in seen_names:
            errs.append(f"{where}: duplicate project name (also {seen_names[nk]!r})")
        seen_names[nk] = r["name"]
    return errs, warns

def validate_order(rows):
    warns = []
    from itertools import groupby
    key = lambda r: (r["cat"], r["sub"])
    idx = {c: i for i, c in enumerate(generate.CAT_ORDER)}
    for (cat, sub), grp in groupby(rows, key=key):
        grp = list(grp)
        names = [norm(r["name"]) for r in grp]
        if names != sorted(names):
            warns.append(f"{cat} › {sub}: entries are not alphabetical")
    return warns

def validate_readme(rows):
    """Fail if README.md is stale relative to the dataset."""
    want = generate.render(rows)
    have = README.read_text(encoding="utf-8") if README.exists() else ""
    if want != have:
        return ["README.md is out of date — run `make build` and commit the result"]
    return []

def check_links(rows, sample=None, workers=32, timeout=12):
    """Check project URLs without turning transient network failures into false dead-link reports.

    Only HTTP 404/410 are treated as confirmed dead links. Rate limits, access blocks,
    upstream 5xx responses, DNS/TLS failures, and timeouts are reported as transient so
    scheduled CI remains useful rather than flaky.
    """
    urls = []
    for r in rows:
        urls += [r["url"]] + (r.get("alt") or [])
    urls = sorted(set(urls))
    if sample:
        random.seed(0)
        urls = random.sample(urls, min(sample, len(urls)))

    def request(u):
        headers = {"User-Agent": "opensource-atlas-linkcheck/1.0", "Accept": "text/html,*/*;q=0.8"}
        for method in ("HEAD", "GET"):
            req = urllib.request.Request(u, method=method, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return u, "ok", resp.status, resp.geturl()
            except urllib.error.HTTPError as e:
                # Retry GET when HEAD is commonly blocked or rate-limited.
                if method == "HEAD" and e.code in (403, 405, 429):
                    continue
                if e.code in (404, 410):
                    return u, "dead", e.code, str(e)
                return u, "transient", e.code, str(e)
            except Exception as e:
                # A GET retry rarely helps a transport failure and doubles worst-case time.
                return u, "transient", "ERR", str(e)
        return u, "transient", "ERR", "request rejected by upstream"

    dead, moved, transient = [], [], []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for u, kind, status, final in ex.map(request, urls):
            if kind == "dead":
                dead.append((u, status, final))
            elif kind == "transient":
                transient.append((u, status, final))
            elif final and final.rstrip("/") != u.rstrip("/"):
                moved.append((u, final))
    return dead, moved, transient

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--links", action="store_true", help="HTTP-check every URL")
    ap.add_argument("--sample", type=int, default=None, help="only check N random links")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()

    rows = load()
    errs, warns = validate_schema(rows)
    warns += validate_order(rows)
    errs += validate_readme(rows)

    print(f"Loaded {len(rows)} projects.")
    for w in warns: print(f"  warning: {w}")
    for e in errs: print(f"  ERROR:   {e}")

    if args.links:
        print("Checking links (this can take a minute)…")
        dead, moved, transient = check_links(rows, sample=args.sample)
        for u, final in moved:
            print(f"  moved:     {u} -> {final}")
        for u, status, msg in transient:
            print(f"  transient: [{status}] {u}  {msg}")
        for u, status, msg in dead:
            print(f"  DEAD:      [{status}] {u}  {msg}")
            errs.append(f"dead link: {u} ({status})")

    fail = bool(errs) or (args.strict and bool(warns))
    print("\n" + ("FAILED" if fail else "OK") +
          f" — {len(errs)} errors, {len(warns)} warnings.")
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
