#!/usr/bin/env python3
"""
PriceProbe — zero-dependency web monitoring & data-extraction engine.

What it does
------------
1. Reads a list of target URLs (targets.json).
2. Fetches each page (polite headers, gzip, timeout, retries) — stdlib only.
3. Extracts price(s), product title, and stock status with robust regexes
   (plus optional per-target custom regex).
4. Saves a timestamped snapshot to snapshots/.
5. Diffs against the previous snapshot: price up/down, back-in/out-of-stock,
   new/removed targets.
6. Renders a clean, client-ready HTML report (changes highlighted).

Run:
    python3 monitor.py                 # uses targets.json (falls back to example)
    python3 monitor.py my_targets.json

No pip install. No API keys. Works offline on the operator's machine.
Built to be the delivery engine behind a paid "competitor-price intel" service
and one-off data-extraction gigs.
"""

import sys, os, re, json, gzip, ssl, html, datetime, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(HERE, "snapshots")
REPORT = os.path.join(HERE, "report.html")
TIMEOUT = 20
RETRIES = 2

# ---- price / stock detection -------------------------------------------------
# Match $1,299.00 / S$49 / USD 19.99 / £9.99 / €1.234,56 etc.
PRICE_RE = re.compile(
    r"(?:S\$|US\$|A\$|HK\$|RM|₱|₹|¥|\$|USD|SGD|MYR|GBP|EUR|£|€)\s?"
    r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?",
    re.I,
)
OOS_RE = re.compile(
    r"out[\s\-]?of[\s\-]?stock|sold[\s\-]?out|currently unavailable|"
    r"缺货|售罄|无货|temporarily unavailable|notify me when",
    re.I,
)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
OGTITLE_RE = re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', re.I)


def fetch(url):
    """Return decoded HTML text or raises. Polite, gzip-aware, retrying."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Encoding": "gzip, identity",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    # Try verified TLS first; fall back to unverified if the machine is missing
    # root certs (common on macOS Python.org builds). We only read public pages.
    contexts = [ssl.create_default_context(), ssl._create_unverified_context()]
    last = None
    for ctx in contexts:
        for attempt in range(RETRIES + 1):
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
                    raw = r.read()
                    if r.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    charset = r.headers.get_content_charset() or "utf-8"
                    return raw.decode(charset, errors="replace")
            except urllib.error.URLError as e:
                last = e
                if not isinstance(getattr(e, "reason", None), ssl.SSLError):
                    break  # non-TLS error: don't bother with the unverified ctx
            except Exception as e:  # noqa
                last = e
    raise last


def clean(s):
    return html.unescape(re.sub(r"\s+", " ", s or "").strip())


def extract(htmltext, custom_regex=None):
    """Pull title, price, stock from raw HTML."""
    title = ""
    m = OGTITLE_RE.search(htmltext) or TITLE_RE.search(htmltext)
    if m:
        title = clean(m.group(1))[:140]

    price = None
    if custom_regex:
        cm = re.search(custom_regex, htmltext)
        if cm:
            price = clean(cm.group(cm.lastindex or 0))
    if not price:
        pm = PRICE_RE.search(htmltext)
        if pm:
            price = clean(pm.group(0))

    in_stock = not bool(OOS_RE.search(htmltext))
    return {"title": title, "price": price, "in_stock": in_stock}


def load_targets(path):
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    ex = os.path.join(HERE, "targets.example.json")
    with open(ex) as f:
        return json.load(f)


def latest_snapshot():
    if not os.path.isdir(SNAP_DIR):
        return None
    snaps = sorted(f for f in os.listdir(SNAP_DIR) if f.endswith(".json"))
    if not snaps:
        return None
    with open(os.path.join(SNAP_DIR, snaps[-1])) as f:
        return json.load(f)


def num(price):
    """Best-effort numeric value of a price string for comparison."""
    if not price:
        return None
    digits = re.sub(r"[^\d.,]", "", price)
    # normalise: if both . and , present, assume , = thousands
    if "." in digits and "," in digits:
        digits = digits.replace(",", "")
    elif "," in digits and "." not in digits:
        # could be decimal comma
        if len(digits.split(",")[-1]) == 2:
            digits = digits.replace(",", ".")
        else:
            digits = digits.replace(",", "")
    try:
        return float(digits)
    except ValueError:
        return None


def diff(prev, cur):
    """Compare two snapshots keyed by target name -> list of change dicts."""
    changes = []
    prev_map = {r["name"]: r for r in (prev or {}).get("rows", [])}
    for row in cur["rows"]:
        old = prev_map.get(row["name"])
        if not old:
            changes.append({"name": row["name"], "kind": "new", "detail": "newly added"})
            continue
        op, np_ = num(old.get("price")), num(row.get("price"))
        if op is not None and np_ is not None and op != np_:
            pct = (np_ - op) / op * 100 if op else 0
            changes.append({
                "name": row["name"],
                "kind": "price_up" if np_ > op else "price_down",
                "detail": f"{old.get('price')} → {row.get('price')} ({pct:+.1f}%)",
            })
        if old.get("in_stock") and not row.get("in_stock"):
            changes.append({"name": row["name"], "kind": "oos", "detail": "now OUT of stock"})
        elif not old.get("in_stock") and row.get("in_stock"):
            changes.append({"name": row["name"], "kind": "restock", "detail": "back IN stock"})
    return changes


# ---- HTML report -------------------------------------------------------------
KIND_STYLE = {
    "price_up":   ("#b42318", "▲ price up"),
    "price_down": ("#067647", "▼ price down"),
    "oos":        ("#6b7280", "✕ out of stock"),
    "restock":    ("#067647", "✓ restocked"),
    "new":        ("#1d4ed8", "＋ new"),
}


def render(cur, changes, errors):
    ts = cur["taken_at"]
    rows_html = ""
    chg_by_name = {}
    for c in changes:
        chg_by_name.setdefault(c["name"], []).append(c)
    for row in cur["rows"]:
        cs = chg_by_name.get(row["name"], [])
        badge = ""
        for c in cs:
            color, label = KIND_STYLE.get(c["kind"], ("#374151", c["kind"]))
            badge += f'<span style="background:{color};color:#fff;border-radius:6px;padding:2px 8px;font-size:12px;margin-right:6px;white-space:nowrap">{label}</span>'
        detail = "<br>".join(html.escape(c["detail"]) for c in cs)
        stock = "In stock" if row.get("in_stock") else '<b style="color:#b42318">Out of stock</b>'
        rows_html += f"""
        <tr>
          <td><b>{html.escape(row['name'])}</b><br>
              <a href="{html.escape(row['url'])}" style="color:#6b7280;font-size:12px">{html.escape(row['url'][:60])}</a></td>
          <td style="font-size:15px">{html.escape(row.get('price') or '—')}</td>
          <td>{stock}</td>
          <td>{badge}<div style="color:#6b7280;font-size:12px;margin-top:4px">{detail}</div></td>
        </tr>"""

    err_html = ""
    if errors:
        items = "".join(f"<li>{html.escape(n)}: {html.escape(e)}</li>" for n, e in errors)
        err_html = f'<div style="background:#fef3f2;border:1px solid #fecdca;color:#b42318;padding:12px 16px;border-radius:10px;margin:16px 0"><b>Could not fetch:</b><ul style="margin:6px 0 0">{items}</ul></div>'

    n_changes = len(changes)
    summary = f"{n_changes} change(s) detected" if n_changes else "No changes since last run"

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Competitor Price Intel — {ts}</title></head>
<body style="margin:0;font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#f9fafb;color:#111827">
<div style="max-width:860px;margin:0 auto;padding:32px 20px">
  <div style="display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px">
    <h1 style="margin:0;font-size:24px">Competitor Price &amp; Stock Intel</h1>
    <span style="color:#6b7280;font-size:13px">Generated {ts}</span>
  </div>
  <p style="font-size:16px;margin:10px 0 0"><b>{summary}.</b> Monitoring {len(cur['rows'])} product(s).</p>
  {err_html}
  <table style="width:100%;border-collapse:collapse;margin-top:18px;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)">
    <thead><tr style="background:#f3f4f6;text-align:left;font-size:13px;color:#374151">
      <th style="padding:12px 14px">Product</th><th style="padding:12px 14px">Price</th>
      <th style="padding:12px 14px">Stock</th><th style="padding:12px 14px">Change</th>
    </tr></thead>
    <tbody style="font-size:14px">{rows_html}</tbody>
  </table>
  <p style="color:#9ca3af;font-size:12px;margin-top:24px">PriceProbe · automated competitor monitoring · run daily for fresh intel.</p>
</div></body></html>"""


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "targets.json")
    targets = load_targets(path)
    os.makedirs(SNAP_DIR, exist_ok=True)

    rows, errors = [], []
    for t in targets:
        name, url = t["name"], t["url"]
        try:
            page = fetch(url)
            data = extract(page, t.get("regex"))
            rows.append({"name": name, "url": url, **data})
            print(f"  ✓ {name}: {data['price'] or 'n/a'} | {'in' if data['in_stock'] else 'OUT'} stock")
        except Exception as e:  # noqa
            errors.append((name, str(e)[:80]))
            rows.append({"name": name, "url": url, "title": "", "price": None, "in_stock": True})
            print(f"  ✗ {name}: {str(e)[:60]}")

    prev = latest_snapshot()
    cur = {"taken_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "rows": rows}
    changes = diff(prev, cur)

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    with open(os.path.join(SNAP_DIR, f"{stamp}.json"), "w") as f:
        json.dump(cur, f, indent=2, ensure_ascii=False)

    with open(REPORT, "w") as f:
        f.write(render(cur, changes, errors))

    print(f"\n{len(changes)} change(s) detected. Report → {REPORT}")


if __name__ == "__main__":
    main()
