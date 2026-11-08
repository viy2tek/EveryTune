"""Snapshot link metadata, not scraping music results or bypassing access controls."""
import json
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import urllib.request
from urllib.parse import urlparse


class CatalogueParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = {}
        self.anchor = None
        self.heading = None
        self.section = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("h2", "h3", "h4"):
            self.heading = []
        if tag == "a" and attrs.get("href", "").startswith("https://"):
            self.anchor = {"url": attrs["href"], "label": "", "section": self.section}

    def handle_data(self, data):
        if self.heading is not None:
            self.heading.append(data)
        if self.anchor is not None:
            self.anchor["label"] += data

    def handle_endtag(self, tag):
        if tag in ("h2", "h3", "h4") and self.heading is not None:
            self.section = " ".join("".join(self.heading).replace("\u200b", "").split())
            self.heading = None
        if tag == "a" and self.anchor is not None:
            link = self.anchor
            self.anchor = None
            if link["section"] and link["label"].strip() and urlparse(link["url"]).hostname not in {"fmhy.net", "fmhy.xyz"}:
                link["label"] = " ".join(link["label"].split())
                link["classification"] = "inventário; integração não avaliada"
                self.links.setdefault(link["url"], link)


def main():
    url = "https://fmhy.net/audio"
    request = urllib.request.Request(url, headers={"User-Agent": "EveryTune/0.1 (source catalogue inventory)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")
    parser = CatalogueParser()
    parser.feed(html)
    assert len(parser.links) > 20, "Unexpected FMHY page structure; inspect before using inventory"
    output = Path(__file__).resolve().parent.parent / "docs" / "fmhy-audio-links.json"
    output.write_text(json.dumps({"catalogue": url, "checked_on": date.today().isoformat(), "note": "Inventário de links, incluindo ferramentas e espelhos; não implica API, licença ou segurança verificadas.", "links": list(parser.links.values())}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(parser.links)} links registrados em {output}")


if __name__ == "__main__":
    main()
