---
title: Every Shopify store exposes these 4 public URLs — here's what a competitor sees in 30 seconds
published: false
tags: ecommerce, shopify, webscraping, python
---

Most Shopify merchants assume their catalog, pricing logic, and store structure are only visible through their storefront. They're not. Shopify serves several JSON and XML endpoints publicly *by design* — the same data its own theme uses — and anyone can read them without a login, an API key, or a scraping tool.

This isn't a hack or a vulnerability. It's public, intentional, and useful (it's how apps and themes work). But most store owners have never looked at what it reveals. Here are the four endpoints, what each one shows, and how to check your own store in 30 seconds.

## 1. `/products.json` — your entire catalog and live prices

```
https://any-store.com/products.json?limit=250
```

Returns every product, every variant, every price, in clean JSON. Titles, options, inventory-ish signals, images, and the exact price a competitor would need to undercut you. Paginate with `?page=2` and you get the whole catalog, however big.

I covered the pricing angle in detail [in a previous post](https://dev.to/willylam2222/i-pulled-800-competitor-prices-from-4-shopify-stores-in-8-seconds-with-20-lines-of-python-no-2kfi) — the short version: a competitor can snapshot your full price list in seconds and diff it daily.

## 2. `/collections.json` — how you merchandise

```
https://any-store.com/collections.json
```

Every collection you've built: "Best Sellers," "Sale," "New Arrivals," seasonal drops. This is your merchandising strategy laid out — which products you group, what you're pushing, how you segment. A competitor learns what you *think* sells, not just what you stock.

## 3. `/meta.json` — your store's identity

```
https://any-store.com/meta.json
```

Returns the store's name, ID, and location fields (city, province, country). Usually harmless — it's business info that's often on your contact page anyway — but worth knowing it's queryable programmatically, which is how tools bucket and geo-tag stores at scale.

## 4. `/sitemap.xml` — every URL, including things you forgot were live

```
https://any-store.com/sitemap.xml
```

Shopify auto-generates a sitemap of every product, collection, and page. It's meant for Google, but it's also a complete map of your store for anyone. Occasionally it surfaces pages a merchant assumed were "hidden" (unlinked but still published). If it's not truly unpublished, it's in here.

## Check your own store right now

Open each URL with your own domain. Whatever you see is exactly what every competitor, analyst, and bot can see too. That's the point — these power legitimate integrations — but you should know what's on the table.

If you want to see it programmatically, this reads all four with no dependencies:

```python
import json, ssl, urllib.request, urllib.error

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for ctx in (ssl.create_default_context(), ssl._create_unverified_context()):
        try:
            return urllib.request.urlopen(req, timeout=25, context=ctx).read().decode("utf-8", "replace")
        except urllib.error.URLError:
            continue

store = "https://onyxcoffeelab.com"   # <- put any Shopify store here
for path in ["/products.json?limit=1", "/collections.json", "/meta.json", "/sitemap.xml"]:
    body = get(store + path)
    print(path, "->", len(body), "bytes")
```

## What to actually do with this

**If you sell:** you can't wall these off (Shopify serves them), so the play isn't hiding — it's *watching*. Since your competitors' data is equally open, monitor it. Know when a rival drops a price or sells out, because that's your window to react.

**If you're technical:** the free, open-source version that snapshots and diffs a competitor over time is here — [github.com/willylam2222-bot/priceprobe](https://github.com/willylam2222-bot/priceprobe).

**If you'd rather not touch code:** send me a few competitor URLs and I'll send back a clean report of their current prices, stock, and recent moves — [willyverse188.gumroad.com/l/kphhe](https://willyverse188.gumroad.com/l/kphhe).

The data is already public on both sides. The only question is who's actually looking.
