#!/usr/bin/env python3
"""
PriceProbe notifier — push an alert the moment a competitor's price or stock changes.

Runs right after monitor.py. Reads the two newest snapshots, diffs them, and if
anything moved, POSTs a summary to a webhook (Slack, Discord, or any endpoint
that accepts JSON). Zero dependencies — Python standard library only.

    python3 monitor.py && python3 notify.py

Set your webhook once (Slack "Incoming Webhook" or Discord channel webhook):
    export PRICEPROBE_WEBHOOK="https://hooks.slack.com/services/XXX/YYY/ZZZ"

No webhook set? It just prints the changes — perfect for cron + `mail`.
"""
import os, sys, glob, json, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(HERE, "snapshots")

try:
    from monitor import diff  # reuse the exact same change-detection logic
except Exception:
    diff = None


def latest_two():
    files = sorted(glob.glob(os.path.join(SNAP_DIR, "*.json")))
    if len(files) < 2:
        return None, (json.load(open(files[-1])) if files else None)
    return json.load(open(files[-2])), json.load(open(files[-1]))


def local_diff(prev, cur):
    """Fallback diff if monitor.diff isn't importable."""
    changes, pm = [], {r["name"]: r for r in (prev or {}).get("rows", [])}
    for row in cur.get("rows", []):
        old = pm.get(row["name"])
        if not old:
            changes.append({"name": row["name"], "kind": "new", "detail": "newly added"}); continue
        if old.get("price") and row.get("price") and old["price"] != row["price"]:
            changes.append({"name": row["name"], "kind": "price",
                            "detail": f"{old['price']} → {row['price']}"})
        if old.get("in_stock") and not row.get("in_stock"):
            changes.append({"name": row["name"], "kind": "oos", "detail": "now OUT of stock"})
        elif not old.get("in_stock") and row.get("in_stock"):
            changes.append({"name": row["name"], "kind": "restock", "detail": "back IN stock"})
    return changes


ICON = {"price_up": "🔺", "price_down": "🔻", "price": "🔀",
        "oos": "⛔", "restock": "✅", "new": "🆕"}


def post(url, text):
    # Slack uses {"text":...}; Discord uses {"content":...}. Send both — each ignores the other.
    data = json.dumps({"text": text, "content": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=15).read()


def main():
    prev, cur = latest_two()
    if not cur:
        print("No snapshots yet — run monitor.py first."); return
    changes = (diff or local_diff)(prev, cur)
    if not changes:
        print("PriceProbe: no changes since last run."); return

    lines = [f"*PriceProbe* — {len(changes)} change(s) detected:"]
    for c in changes:
        lines.append(f"{ICON.get(c['kind'], '•')} *{c['name']}* — {c['detail']}")
    text = "\n".join(lines)

    hook = os.environ.get("PRICEPROBE_WEBHOOK", "").strip()
    if hook:
        try:
            post(hook, text); print(f"Alerted {len(changes)} change(s) → webhook.")
        except urllib.error.URLError as e:
            print(f"Webhook failed ({e}); changes below:\n{text}"); sys.exit(1)
    else:
        print(text)  # no webhook: print for cron/mail piping


if __name__ == "__main__":
    main()
