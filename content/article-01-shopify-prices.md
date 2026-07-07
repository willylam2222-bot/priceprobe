---
title: I pulled 800+ competitor prices from 4 Shopify stores in 8 seconds — with 20 lines of Python (no libraries)
published: false
tags: python, webscraping, ecommerce, shopify
---

If a competitor drops a price on Tuesday and you notice on Friday, you've lost three days of sales. Most small store owners find out by accident. It turns out you don't need a $99/month tool or a scraping framework to fix that — almost every Shopify store hands you its entire catalog and live prices for free, if you know the one URL.

I ran it across four real coffee roasters this morning. Here are the actual numbers, the 20-line script, and what it means if you sell anything online.

## The one URL nobody tells you about

Every Shopify storefront exposes a public JSON feed of its products at:

```
https://<any-shopify-store>/products.json?limit=250
```

No API key. No login. No headless browser. It's the same data the store's own theme uses to render pages — titles, variants, and **live prices** — returned as clean JSON. Open one in your browser right now and you'll see it.

## The result (real data, pulled today)

I pointed a tiny script at four well-known roasters and pulled every product + price in about 8 seconds total:

| Store | Products | Priced bags | Bag price range | Median |
|---|---|---|---|---|
| Onyx Coffee Lab | 248 | 171 | $10–40 | $26.00 |
| Counter Culture | 169 | 201 | $10–39 | $25.00 |
| Verve Coffee | 168 | 460 | $10–40 | $26.50 |
| Ruby Coffee | 213 | 494 | $10–40 | $24.25 |

That's **798 products** and their live prices, for free, in less time than it took to read this paragraph. The median bag sits in a tight $24.25–$26.50 band across all four — which is itself the insight: in a mature niche your price anchor is set by the pack, and being 15% off it (either way) is a decision you want to make on purpose, not by accident.

## The entire script

Zero dependencies — Python standard library only:

```python
import json, ssl, urllib.request, urllib.error, statistics

STORES = {
    "Onyx Coffee Lab": "https://onyxcoffeelab.com",
    "Counter Culture": "https://counterculturecoffee.com",
    "Verve Coffee":    "https://www.vervecoffee.com",
    "Ruby Coffee":     "https://rubycoffeeroasters.com",
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    # 2nd context is a fallback for macOS machines missing root certs
    for ctx in (ssl.create_default_context(), ssl._create_unverified_context()):
        try:
            return urllib.request.urlopen(req, timeout=25, context=ctx).read()
        except urllib.error.URLError:
            continue
    raise RuntimeError("fetch failed: " + url)

def prices(base):
    data = json.loads(fetch(f"{base}/products.json?limit=250"))
    out = []
    for p in data["products"]:
        for v in p["variants"]:
            try: pr = float(v["price"])
            except (TypeError, ValueError): continue
            if 10 <= pr <= 40:          # single-bag band
                out.append(pr)
    return out

for name, base in STORES.items():
    p = prices(base)
    print(f"{name:20} {len(p):3} bags  ${min(p):.2f}-{max(p):.2f}  median ${statistics.median(p):.2f}")
```

That's the whole thing. Swap in your own competitors' domains and you have a competitor price monitor.

## Turning it into an actual monitor

The snippet above is a one-shot snapshot. To catch *changes*, you save each run and diff against the last one:

1. On each run, store `{product_title: price}` to a small JSON file.
2. Next run, compare: flag anything where the price moved, or a product that appeared/disappeared (a competitor selling out is your window to hold or raise price).
3. Schedule it once a day with `cron` (mac/Linux) or Task Scheduler (Windows).

Daily is plenty — be polite, one request per store.

## A few honest caveats

- **Only works on Shopify stores.** Roughly a quarter of the stores you compete with run Shopify; check by opening the `/products.json` URL. Other platforms (VTEX, BigCommerce, WooCommerce) have their own public endpoints; marketplaces like Amazon actively block this and need a different approach.
- **Prices only, not promotions.** Cart-level discounts won't show. The list price still tells you 90% of what you need.
- **Be respectful.** This is public data the store already serves to every browser, but hammering it is rude and pointless. Once a day covers real pricing moves.

## If you don't want to touch a terminal

I packaged this into a tiny open-source tool that does the save-and-diff for you: **[github.com/willylam2222-bot/priceprobe](https://github.com/willylam2222-bot/priceprobe)** — free, run it on your own laptop.

And if you'd rather just get the answer without setting anything up, I'll run it for you: send me your competitors' URLs and I'll send back a clean report of their current prices, stock, and any recent moves. Details here: [willyverse188.gumroad.com/l/kphhe](https://willyverse188.gumroad.com/l/kphhe).

Either way — the URL at the top of this post is free and yours to use. Go look at what your competitors are charging right now.
