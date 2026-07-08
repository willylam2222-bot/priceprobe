---
title: The Shopify products.json endpoint — a complete, practical guide (2026)
published: false
tags: shopify, webscraping, ecommerce, api
---

Every Shopify store publishes a JSON feed of its catalog at `/products.json`. It needs no API key, no app, and no authentication — it's the same data the storefront theme reads. This is the single most useful endpoint for anyone doing price monitoring, catalog analysis, or competitor research on Shopify, and it's badly under-documented. Here's everything it actually returns and how to use it.

## The URL

```
https://any-store.com/products.json
```

By default it returns the first 30 products. Two query params matter:

- `?limit=250` — the maximum page size (250 is the hard cap; asking for more still gives 250).
- `?page=2` — paginate. Keep incrementing until you get an empty `products` array.

So the full catalog of a large store is just a loop:

```python
import json, ssl, time, urllib.request, urllib.error

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for ctx in (ssl.create_default_context(), ssl._create_unverified_context()):
        try:
            return urllib.request.urlopen(req, timeout=25, context=ctx).read()
        except urllib.error.URLError:
            continue
    raise RuntimeError("fetch failed: " + url)   # fail loudly, don't return None

def all_products(base):
    page, out = 1, []
    while True:
        data = json.loads(fetch(f"{base}/products.json?limit=250&page={page}"))
        batch = data.get("products", [])
        if not batch:
            break
        out += batch
        page += 1
        time.sleep(0.5)                            # be polite between pages
    return out

products = all_products("https://onyxcoffeelab.com")
print(len(products), "products")
```

## What each product contains

A product object has these fields:

| Field | What it's for |
|---|---|
| `id` | Stable Shopify product ID |
| `title` | Product name |
| `handle` | URL slug (`/products/<handle>`) |
| `vendor` | Brand |
| `product_type` | Category |
| `tags` | Merchandising tags |
| `body_html` | Full description (HTML) |
| `published_at` / `updated_at` | When it went live / last changed |
| `variants` | The array that actually holds prices |
| `images` | Image URLs |
| `options` | Variant option names (Size, Grind, etc.) |

## The variant fields (where the money is)

Prices live on **variants**, not the product. Each variant gives you:

| Field | Why it matters |
|---|---|
| `price` | The current selling price (string, e.g. `"26.00"`) |
| `compare_at_price` | The "was" price — **if this is set and higher than `price`, the item is on sale**. This is how you detect promotions. |
| `available` | Boolean in/out of stock. (Note: it's a boolean, not a quantity.) |
| `sku` | The store's SKU — useful for matching the same product across stores |
| `grams` | Shipping weight |
| `option1/2/3` | The variant values (e.g. "12oz", "Whole Bean") |
| `updated_at` | Timestamp — diff this between runs to catch changes cheaply |

## Three things you can build in an afternoon

1. **Price monitor** — save `{sku: price}` each run, diff against last run, alert on changes.
2. **Sale detector** — flag any variant where `compare_at_price > price`. You now know exactly what a competitor is discounting and by how much.
3. **Stock watch** — track `available` flipping to `false`; a competitor selling out is your window to hold or raise price.

## Honest limits

- **Published products only.** Drafts and unpublished items don't appear.
- **`available` is a boolean, not a count.** You can't see *how many* are left, just in/out of stock.
- **Prices, not cart discounts.** Automatic cart-level or code-based discounts won't show — but `compare_at_price` covers standard sale pricing.
- **Not every store is Shopify.** Check by opening the URL; if you get JSON, it's Shopify. Other platforms (VTEX, BigCommerce) have their own public endpoints.
- **Be polite.** This is public data, but hammering it is pointless — once a day catches real pricing moves.

## Turn it into something you'll actually use

The open-source tool that does the save-and-diff (price + sale + stock) for you is here: [github.com/willylam2222-bot/priceprobe](https://github.com/willylam2222-bot/priceprobe). If you'd rather just get the answer, send me a few competitor URLs and I'll return a clean report of their prices, sales, and stock: [willyverse188.gumroad.com/l/kphhe](https://willyverse188.gumroad.com/l/kphhe).

The endpoint is public and free. Now you know exactly what's in it.
