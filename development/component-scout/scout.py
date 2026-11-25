#!/usr/bin/env python3
"""Search the user's bookmarked UI component libraries for ready-made components.

Usage:
  python3 -I scout.py "pricing table" "testimonial" [--per-source 4] [--only planes,skecher] [--refresh]
  python3 -I scout.py --list          # show sources and how many items each indexed

Each library's machine-readable index (shadcn registry.json, llms.txt, sitemap) is
downloaded once and cached for 7 days in ~/.cache/component-scout. 21st.dev is
queried live per search term.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

CACHE = os.path.expanduser("~/.cache/component-scout")
TTL = 7 * 24 * 3600
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131 Safari/537.36"
SHADCN = "npx shadcn@latest add "

# One entry per bookmarked library. `stack` tells the agent whether it fits the project.
SOURCES = {
    "aceternity": dict(stack="shadcn+tailwind+motion", home="https://ui.aceternity.com",
                       llms="https://ui.aceternity.com/llms.txt", llms_filter=("/components/", "/blocks/")),
    "shadcnblocks": dict(stack="shadcn+tailwind (many blocks are Pro)", home="https://www.shadcnblocks.com",
                         registry="https://www.shadcnblocks.com/r/registry.json",
                         install=SHADCN + "https://www.shadcnblocks.com/r/{name}.json",
                         page="https://www.shadcnblocks.com/block/{name}"),
    "spaceui": dict(stack="shadcn+tailwind v4", home="https://www.spaceui.one",
                    registry="https://spaceui.one/r/registry.json",
                    install=SHADCN + "https://spaceui.one/r/{name}.json",
                    page_fn=lambda n: "https://www.spaceui.one/" + (
                        re.sub(r"^demo-p-(.+?)(-\d+)?$", r"primitives/\1", n) if n.startswith("demo-p-") else
                        re.sub(r"^demo-c-(.+?)(-\d+)?$", r"components/\1", n) if n.startswith("demo-c-") else
                        re.sub(r"^block-(.+?)(-\d+)?$", r"blocks/\1", n) if n.startswith("block-") else
                        re.sub(r"^components-spaceui-(.+)$", r"components/\1", n))),
    "componentry": dict(stack="shadcn+tailwind+motion", home="https://componentry.dev",
                        registry="https://componentry.fun/r/registry.json",
                        llms="https://componentry.fun/llms.txt",
                        install=SHADCN + "https://componentry.fun/r/{name}.json",
                        page="https://componentry.dev/docs/components/{name}"),
    "skecher": dict(stack="shadcn+tailwind+motion", home="https://skecher-ui.com",
                    registry="https://skecher-ui.com/r/registry.json",
                    install=SHADCN + "https://skecher-ui.com/r/{name}.json",
                    page="https://skecher-ui.com/docs/{name}"),
    "planes": dict(stack="shadcn+tailwind, WebGL/motion (most are Pro)", home="https://useplanes.com",
                   registry="https://useplanes.com/r/registry.json",
                   install=SHADCN + "https://useplanes.com/r/{name}.json",
                   install_pro="npx shadcn@latest add @useplanes/{name}  (needs Planes Pro key)",
                   page="https://useplanes.com/components/{name}"),
    "boardui": dict(stack="shadcn-style registry, dashboards + AI UI", home="https://www.boardui.com",
                    registry="https://boardui.com/r/registry.json",
                    install=SHADCN + "https://boardui.com/r/{name}.json",
                    page="https://www.boardui.com/components/{name}"),
    "neobrutalism": dict(stack="shadcn+tailwind, neobrutalist style", home="https://www.neobrutalism.dev",
                         sitemap="https://www.neobrutalism.dev/sitemap.xml", sitemap_re=r"/docs/([a-z0-9-]+)$",
                         install=SHADCN + "https://www.neobrutalism.dev/r/{name}.json",
                         page="https://www.neobrutalism.dev/docs/{name}"),
    "prompt-kit": dict(stack="shadcn+tailwind, AI chat UI", home="https://www.prompt-kit.com",
                       llms="https://www.prompt-kit.com/llms.txt", llms_filter="components/",
                       install=SHADCN + '"https://www.prompt-kit.com/c/{name}.json"',
                       page="https://www.prompt-kit.com/docs/{name}"),
    "heroui": dict(stack="HeroUI npm package (@heroui/react), not shadcn", home="https://heroui.com",
                   llms="https://heroui.com/llms.txt", llms_filter="/components/"),
    "mantine-ui": dict(stack="Mantine (@mantine/core) projects only", home="https://ui.mantine.dev",
                       html="https://ui.mantine.dev/", html_re=r'href="/category/([a-z0-9-]+)/?"',
                       page="https://ui.mantine.dev/category/{name}/"),
    "lucide": dict(stack="icons: lucide-react", home="https://lucide.dev",
                   tags="https://unpkg.com/lucide-static@latest/tags.json",
                   page="https://lucide.dev/icons/{name}"),
    "21st": dict(stack="community shadcn/tailwind components (live search)", home="https://21st.dev",
                 live="https://21st.dev/community/components/s/{slug}.md"),
}


def fetch(url, refresh=False, cache=True):
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9.]+", "_", url))
    if cache and not refresh and os.path.exists(path) and time.time() - os.path.getmtime(path) < TTL:
        with open(path, encoding="utf-8") as f:
            return f.read()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("utf-8", "replace")
    if cache:
        os.makedirs(CACHE, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return text


def item(src, name, title="", desc="", cats=(), tier="", page=None):
    s = SOURCES[src]
    rec = dict(source=src, name=name, title=title or name, desc=(desc or "").strip(), cats=list(cats or []), tier=tier)
    rec["page"] = page or (s["page_fn"](name) if "page_fn" in s else s["page"].format(name=name) if "page" in s else s["home"])
    if tier == "pro" and "install_pro" in s:
        rec["install"] = s["install_pro"].format(name=name)
    elif "install" in s:
        rec["install"] = s["install"].format(name=name)
    return rec


MD_LINK = re.compile(r"^\s*-\s*\[([^\]]+)\]\(([^)]+)\)(?::\s*(.*))?$")


def load(src, refresh):
    s, out = SOURCES[src], []
    if "registry" in s:
        for it in json.loads(fetch(s["registry"], refresh)).get("items", []):
            if it.get("type") in ("registry:lib", "registry:hook", "registry:style", "registry:theme"):
                continue
            out.append(item(src, it["name"], it.get("title"), it.get("description"), it.get("categories"), it.get("tier", "")))
    if "llms" in s:
        have, pro = {o["name"] for o in out}, False
        filters = s.get("llms_filter", "")
        filters = (filters,) if isinstance(filters, str) else filters
        for line in fetch(s["llms"], refresh).splitlines():
            if line.startswith("#"):
                pro = "pro" in line.lower()
            m = MD_LINK.match(line)
            if not m or not any(f in m.group(2) for f in filters) or "/install" in m.group(2):
                continue
            url = urllib.parse.urljoin(s["home"] + "/", m.group(2))
            slug = re.sub(r"\.(md|tsx)$", "", url.rstrip("/").rsplit("/", 1)[-1])
            if slug in have:  # enrich registry item with docs description
                for o in out:
                    if o["name"] == slug and not o["desc"]:
                        o["desc"] = m.group(3) or ""
                continue
            title = slug if m.group(1).endswith(".tsx") else m.group(1)
            rec = item(src, slug, title, m.group(3), tier="pro" if pro else "", page=None if "page" in s else url)
            if "registry" in s:  # docs-only page (e.g. a collection), not an installable item
                rec.pop("install", None)
                rec["page"] = url
            out.append(rec)
    if "sitemap" in s:
        names = {m.group(1) for loc in re.findall(r"<loc>([^<]+)</loc>", fetch(s["sitemap"], refresh))
                 for m in [re.search(s["sitemap_re"], loc)] if m}
        out += [item(src, n) for n in sorted(names - {"installation", "changelog", "figma", "styling"})]
    if "html" in s:
        out += [item(src, n, n.replace("-", " ")) for n in sorted(set(re.findall(s["html_re"], fetch(s["html"], refresh))))]
    if "tags" in s:
        for name, tags in json.loads(fetch(s["tags"], refresh)).items():
            pascal = "".join(p.capitalize() for p in name.split("-"))
            rec = item(src, name, name, "tags: " + ", ".join(tags))
            rec["install"] = f"import {{ {pascal} }} from 'lucide-react'"
            out.append(rec)
    return out


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def score(rec, terms):
    fields = [(words(rec["title"] + " " + rec["name"].replace("-", " ")), 3), (words(" ".join(rec["cats"])), 2), (words(rec["desc"]), 1)]
    total, hit = 0, 0
    for t in terms:
        best = max((w for toks, w in fields if any(tok.startswith(t) or (len(t) > 4 and t[:-1] in tok) for tok in toks)), default=0)
        total += best + (t in fields[0][0])  # exact word in the title beats a prefix hit
        hit += best > 0
    return total if hit >= max(1, (len(terms) + 1) // 2) else 0


def live_21st(query):
    slug = "-".join(words(query))
    try:
        text = fetch(SOURCES["21st"]["live"].format(slug=slug), cache=False)
    except urllib.error.HTTPError:
        return [], f"no 21st.dev tag '{slug}' (browse https://21st.dev/community/components)"
    rows = []
    for line in text.splitlines():
        m = re.match(r"^- \[([^\]]+)\]\((https://21st\.dev/[^)]+)\)(.*)$", line)
        if m:
            rows.append(dict(source="21st", title=m.group(1), page=m.group(2), desc=m.group(3).strip(" —"), tier="", cats=[]))
    return rows, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("queries", nargs="*")
    ap.add_argument("--per-source", type=int, default=4)
    ap.add_argument("--only", help="comma-separated source names")
    ap.add_argument("--refresh", action="store_true", help="ignore the 7-day cache")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    srcs = [s for s in SOURCES if not a.only or s in a.only.split(",")]
    static = [s for s in srcs if "live" not in SOURCES[s]]

    index, errors = {}, {}
    def safe(s):
        try:
            return s, load(s, a.refresh)
        except Exception as e:  # one dead site must not sink the search
            return s, e
    with ThreadPoolExecutor(8) as pool:
        for s, res in pool.map(safe, static):
            (errors if isinstance(res, Exception) else index)[s] = res

    if a.list or not a.queries:
        for s in srcs:
            n = len(index[s]) if s in index else ("live" if s == "21st" else f"ERROR {errors.get(s)}")
            print(f"{s:13} {str(n):>6}  {SOURCES[s]['stack']}  {SOURCES[s]['home']}")
        return

    for q in a.queries:
        terms = words(q)
        print(f"\n# {q}")
        for s in srcs:
            if s == "21st":
                rows, err = live_21st(q)
                rows = rows[: a.per_source]
                if err:
                    print(f"\n## 21st — {err}")
                    continue
            elif s in errors:
                print(f"\n## {s} — unavailable: {errors[s]}")
                continue
            else:
                ranked = sorted(((score(r, terms), r) for r in index[s]), key=lambda x: (-x[0], len(x[1]["title"])))
                rows = [r for sc, r in ranked if sc][: a.per_source]
            if not rows:
                continue
            print(f"\n## {s}  [{SOURCES[s]['stack']}]")
            for r in rows:
                tier = f" ({r['tier']})" if r.get("tier") else ""
                desc = f" — {r['desc'][:160]}" if r.get("desc") else ""
                print(f"- {r['title']}{tier}{desc}\n  preview: {r['page']}")
                if r.get("install"):
                    print(f"  install: {r['install']}")


if __name__ == "__main__":
    sys.exit(main())
