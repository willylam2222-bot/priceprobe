#!/usr/bin/env python3
"""
Minimal, dependency-free Markdown -> styled HTML for the PriceProbe blog.
Handles the subset used in our articles: frontmatter, #/##/### headings,
fenced code, inline code, **bold**, [links](url), tables, - / 1. lists,
> blockquotes, paragraphs. Wraps output in the site's house style.

Usage: python3 scripts/build_article.py article.md docs/slug.html
"""
import sys, re, html, os

def esc(s): return html.escape(s, quote=False)

def inline(s):
    # code spans first (protect), then bold, then links
    spans = []
    def stash(m):
        spans.append("<code>" + esc(m.group(1)) + "</code>")
        return f"\x00{len(spans)-1}\x00"
    s = re.sub(r"`([^`]+)`", stash, s)
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], s)
    return s

def convert(md):
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        # fenced code
        if ln.startswith("```"):
            lang = ln[3:].strip()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>" + esc("\n".join(buf)) + "</code></pre>")
            continue
        # headings
        m = re.match(r"(#{1,3})\s+(.*)", ln)
        if m:
            lvl = len(m.group(1)); out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>"); i += 1; continue
        # table
        if "|" in ln and i+1 < len(lines) and re.match(r"^\s*\|?[\s:|-]+\|", lines[i+1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            t = ["<table><thead><tr>"] + [f"<th>{inline(h)}</th>" for h in head] + ["</tr></thead><tbody>"]
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t)); continue
        # blockquote
        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip()); i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>"); continue
        # lists
        if re.match(r"^\s*[-*]\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                buf.append(re.sub(r"^\s*[-*]\s+", "", lines[i])); i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ul>"); continue
        if re.match(r"^\s*\d+\.\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                buf.append(re.sub(r"^\s*\d+\.\s+", "", lines[i])); i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ol>"); continue
        # blank
        if not ln.strip():
            i += 1; continue
        # paragraph (gather until blank)
        buf = [ln]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,3}\s|```|>|\s*[-*]\s|\s*\d+\.\s)", lines[i]) and "|" not in lines[i]:
            buf.append(lines[i]); i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    return "\n".join(out)

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · PriceProbe</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{keywords}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<link rel="canonical" href="https://willylam2222-bot.github.io/priceprobe/{slug}">
<style>
  :root{{--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--accent:#4f46e5;--accent2:#4338ca;--bg:#f8fafc}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:#fff;line-height:1.65;-webkit-font-smoothing:antialiased}}
  .wrap{{max-width:720px;margin:0 auto;padding:0 24px}}
  a{{color:var(--accent)}}
  nav{{border-bottom:1px solid var(--line)}}
  nav .wrap{{display:flex;align-items:center;justify-content:space-between;height:64px;max-width:1000px}}
  .logo{{font-weight:800;font-size:19px;letter-spacing:-.02em;text-decoration:none;color:var(--ink)}}
  .logo span{{color:var(--accent)}}
  article{{padding:52px 0 20px}}
  article h1{{font-size:36px;line-height:1.15;letter-spacing:-.02em;margin-bottom:22px}}
  article h2{{font-size:25px;margin:38px 0 12px;letter-spacing:-.01em}}
  article h3{{font-size:19px;margin:28px 0 10px}}
  article p{{margin:0 0 16px;font-size:17px}}
  article ul,article ol{{margin:0 0 16px 24px}}
  article li{{margin-bottom:7px;font-size:17px}}
  article code{{background:#f1f5f9;padding:2px 6px;border-radius:5px;font-size:14px}}
  article pre{{background:#0f172a;color:#e2e8f0;padding:18px 20px;border-radius:12px;overflow-x:auto;margin:0 0 18px}}
  article pre code{{background:none;padding:0;color:inherit;font-size:13.5px;line-height:1.6}}
  article table{{border-collapse:collapse;width:100%;margin:0 0 18px;font-size:15px}}
  article th,article td{{border:1px solid var(--line);padding:8px 12px;text-align:left}}
  article th{{background:var(--bg)}}
  article blockquote{{border-left:3px solid var(--accent);padding:4px 18px;color:var(--muted);margin:0 0 18px}}
  .cta{{display:block;background:var(--accent);color:#fff;text-decoration:none;text-align:center;font-weight:600;padding:15px;border-radius:10px;margin:30px 0;font-size:16px}}
  .backhome{{display:inline-block;margin:8px 0 40px;color:var(--muted);font-size:14px;text-decoration:none}}
  footer{{border-top:1px solid var(--line);padding:34px 0;color:var(--muted);font-size:13px;text-align:center}}
</style>
</head>
<body>
<nav><div class="wrap"><a class="logo" href="./">Price<span>Probe</span></a><a href="https://willyverse188.gumroad.com/l/kphhe" style="font-size:14px;font-weight:600">Get a report →</a></div></nav>
<div class="wrap">
<article>
{body}
<a class="cta" href="https://willyverse188.gumroad.com/l/kphhe">Get a competitor price report — send your URLs, get clean data back →</a>
<a class="backhome" href="./">← More on PriceProbe</a>
</article>
</div>
<footer>PriceProbe · <a href="https://github.com/willylam2222-bot/priceprobe">open-source on GitHub</a> · an independent tool, not affiliated with Shopify</footer>
</body>
</html>
"""

def main():
    src, dst = sys.argv[1], sys.argv[2]
    md = open(src).read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", md, re.S)
    fm, body_md = (m.group(1), m.group(2)) if m else ("", md)
    title = (re.search(r"title:\s*(.+)", fm) or [None, os.path.basename(src)])[1].strip()
    tags = (re.search(r"tags:\s*(.+)", fm) or [None, ""])[1].strip()
    # description = first real paragraph, trimmed
    first_p = next((l.strip() for l in body_md.split("\n") if l.strip() and not l.startswith("#")), "")
    desc = re.sub(r"[`*\[\]]", "", first_p)[:155]
    body_html = convert(body_md.strip())
    slug = os.path.basename(dst)
    out = TEMPLATE.format(title=esc(title), desc=esc(desc), keywords=esc(tags.replace(",", ", ")),
                          slug=slug, body=body_html)
    open(dst, "w").write(out)
    print(f"built {dst}  ({len(out)} bytes)  <- {src}")

if __name__ == "__main__":
    main()
