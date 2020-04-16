#!/usr/bin/env python3

import os, sys, time, io
import json
import requests
import feedparser
import weasyprint as wp
from PIL import Image, ImageChops, ImageOps

# Discord webhook url
WH_URL = ""

DAYS      = 7       # Days to consider
LIMIT     = 50      # Max number of edits
HIDE_BOTS = False   # Hide bot edits
RSS_URL   = f"https://switchbrew.org/w/api.php?\
hidebots={HIDE_BOTS:d}&urlversion=2&days={DAYS}&limit={LIMIT}&action=feedrecentchanges&feedformat=rss"

BACKGROUND = "#f5f5f5"

SLEEP_TIME = 5 * 60 # 5min

def base_url(url: str):
    return url.split("&")[0]

def trim_image(im: Image):
    prev, cur = (), ImageChops.difference(im, Image.new(im.mode, im.size, im.getpixel((0, 0)))).getbbox()
    while prev != cur:
        im = im.crop(cur)
        prev, cur = cur, ImageChops.difference(im, Image.new(im.mode, im.size, im.getpixel((0, 0)))).getbbox()
    return ImageOps.expand(im, border=20, fill=BACKGROUND)

class SwitchbrewRssClient:
    wh_url:      str
    rss_url:     str
    last_entry:  time.struct_time = time.gmtime()
    new_entries: list             = []

    def __init__(self, wh_url, rss_url):
        if not wh_url or not rss_url:
            raise ValueError("Invalid urls")
        self.wh_url  = wh_url
        self.rss_url = rss_url

    def update(self):
        f = feedparser.parse(self.rss_url)
        for e in f.entries:
            if e.published_parsed > self.last_entry:
                self.new_entries.append(e)
        self.last_entry = max([self.last_entry, *(e.published_parsed for e in self.new_entries)])

    def post(self):
        for e in self.new_entries:
            self.post_entry(e)
            self.new_entries.remove(e)

    @staticmethod
    def render_diff(html: str):
        bg_css    = wp.CSS(string=f"body {{ background: {BACKGROUND} }}")   # Add background
        scale_css = wp.CSS(string="@page { size: 15in; }")                  # Specify page size
        doc       = wp.HTML(string=html).render(stylesheets=[bg_css, scale_css])
        png_data, _, _ = doc.copy(doc.pages[:1]).write_png()                # Select first page only

        im = Image.open(io.BytesIO(png_data))
        im = trim_image(im)

        with io.BytesIO() as out:
            im.save(out, format="png")
            return out.getvalue(), len(doc.pages) == 1

    def post_entry(self, e: feedparser.FeedParserDict):
        image, is_render_complete = self.render_diff(e.summary)
        embed = {
            "embeds": [{
                "title": e.title,
                "author": {"name": e.author},
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', e.published_parsed),
                "url": base_url(e.link),
                "color": 0x7289da if is_render_complete else 0xeb6420, # Blue if image shows the whole diff, orange otherwise
                "description": f"[Full diff]({e.link})",
            }]
        }
        render = {
            "file": ("render.png", image, "image/png"),
        }

        print(f"Posting entry {e.title} at {time.asctime(e.published_parsed)}...")
        r = requests.post(self.wh_url, data={"payload_json": json.dumps(embed)}, files=render)
        try:
            r.raise_for_status()
        except Exception as err:
            print(f"Failed to post entry {e.title} ({e.link}) with rc {r.status_code}:\n{err}")

def main(argc, argv):
    global WH_URL
    if not WH_URL:
        with open("webhook.url") as f:
            WH_URL = f.read().strip()

    c = SwitchbrewRssClient(WH_URL, RSS_URL)
    while True:
        c.update()
        c.post()
        print(f"Processed at {time.asctime(time.gmtime())}")
        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
