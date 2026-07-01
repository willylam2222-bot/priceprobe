<div align="center">

# 📡 PriceProbe

**Track any competitor's prices & stock — free, self-hosted, zero dependencies.**

Point it at competitor product URLs → get a clean report of every price drop, hike, and stockout.
No subscription. No API keys. No account. Pure Python standard library.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

</div>

---

## See it in action

![PriceProbe competitor price & stock report](screenshot.png)

*Real output — competitor prices tracked, every change highlighted: ▲ price up, ▼ price down, ✓ restock.*

---

## Why

Most competitor-price tools charge **$40–100/month** to watch a handful of URLs. If you just want to
track a few competitors, that's overkill. PriceProbe is a tiny script you own and run yourself.

## What it does

- Fetches a list of competitor product pages (polite headers, gzip, retries, TLS-fallback)
- Extracts **price**, **title**, and **stock status** with robust regexes
- Diffs against the last run → flags **▲ price up / ▼ price down / ✕ out-of-stock / ✓ restock**
- Renders a clean, shareable **HTML report**

## Quick start

```bash
git clone https://github.com/YOURNAME/priceprobe
cd priceprobe
# edit targets.example.json → your competitor URLs, save as targets.json
python3 monitor.py
open report.html
```

No `pip install`. No config files. Runs anywhere Python 3.8+ runs.

## Example

```json
[
  {"name": "Rival — Blue Hoodie", "url": "https://their-store.com/products/blue-hoodie"},
  {"name": "Rival — Red Cap",     "url": "https://their-store.com/products/red-cap"}
]
```

→ produces a report highlighting exactly what changed since yesterday.

## Automate it

Schedule `python3 monitor.py` with cron (Mac/Linux) or Task Scheduler (Windows) to get a fresh
report every morning. Never miss a competitor's price move again.

---

## 🚀 Don't want to touch the terminal?

This free version is for developers comfortable running a script. If you're a **store owner** who
just wants it to *work* — a one-time **$19** packaged version includes a double-click runner, a
step-by-step guide with screenshots, and email support:

**→ [Get PriceProbe (one-time $19, no subscription)](https://willyverse188.gumroad.com/l/ptzxo)**

Same engine. You're paying for zero-setup convenience, not a monthly rental.

---

## License

MIT — do whatever you want. If it saves you money, a ⭐ is appreciated.

## Contributing

Site hides its price behind JavaScript? Open an issue with the URL and I'll add a matcher.
PRs for new extractors welcome.
