# sources/al3ashq.py
import cloudscraper
from bs4 import BeautifulSoup
import time
import re

class Source:
    name = "Al3ashq (العاشق)"
    base_url = "https://3asq.org"

    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={'custom': 'Mozilla/5.0 (Android) AkhiManga/1.0'}
        )

    def search(self, query):
        results = []
        q = query.replace(" ", "+")
        search_url = f"{self.base_url}/?s={q}"
        r = self.scraper.get(search_url, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        entries = soup.select(".post") or soup.select(".bs") or soup.select(".result-item")
        for e in entries:
            a = e.find("a")
            if not a:
                continue
            title = a.get("title") or a.get_text().strip()
            href = a.get("href")
            if href and title:
                results.append({"title": title, "url": href})
        # fallback basic scan
        if not results:
            for a in soup.select("a"):
                href = a.get("href", "")
                text = (a.get("title") or a.get_text()).strip()
                if query.lower() in text.lower():
                    results.append({"title": text, "url": href})
        time.sleep(1.0)
        return results

    def get_chapters(self, manga_url):
        r = self.scraper.get(manga_url, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        chapters = []
        for sel in [".chapters a", ".post-body a", ".chapter a", ".wp-manga-chapter a"]:
            for a in soup.select(sel):
                href = a.get("href")
                title = a.get_text().strip()
                if href and title:
                    chapters.append({"title": title, "url": href})
            if chapters:
                break
        # dedupe
        seen = set()
        out = []
        for c in chapters:
            if c["url"] in seen:
                continue
            seen.add(c["url"])
            out.append(c)
        time.sleep(0.7)
        return out

    def get_images(self, chapter_url):
        r = self.scraper.get(chapter_url, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        imgs = []
        for sel in [".chapter-img img", ".entry-content img", ".reader img", "img"]:
            for img in soup.select(sel):
                src = img.get("data-src") or img.get("src") or img.get("data-original")
                if src and (src.startswith("http") or src.startswith("//")):
                    if src.startswith("//"):
                        src = "https:" + src
                    imgs.append(src)
            if imgs:
                break
        # Some sites inject JSON with images; attempt to capture simple arrays
        if not imgs:
            scripts = soup.find_all("script")
            for s in scripts:
                txt = s.string
                if not txt:
                    continue
                # naive: find "images: [ 'url1', 'url2' ]"
                m = re.search(r"images\s*:\s*(\[[^\]]+\])", txt)
                if m:
                    arr_txt = m.group(1)
                    # extract urls
                    urls = re.findall(r"https?://[^'\"\\s]+", arr_txt)
                    imgs.extend(urls)
        time.sleep(0.7)
        return imgs
      
