# sources/lekmanga.py
import requests
from bs4 import BeautifulSoup
import time

class Source:
    name = "MangaLik (مانجا ليك)"
    base_url = "https://lekmanga.net"  # adjust if needed

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Android) AkhiManga/1.0"
        })

    def search(self, query):
        """
        return list of dicts: {"title":..., "url":...}
        """
        results = []
        q = query.replace(" ", "+")
        search_url = f"{self.base_url}/?s={q}"
        r = self.session.get(search_url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        # try multiple selectors for robustness
        items = soup.select(".post") or soup.select(".bs") or soup.select(".manga")
        for it in items:
            a = it.find("a")
            if not a:
                continue
            title = a.get("title") or a.get_text().strip()
            href = a.get("href")
            if not href:
                continue
            results.append({"title": title, "url": href})
        # fallback: parse search result links
        if not results:
            for a in soup.select("a"):
                href = a.get("href", "")
                text = (a.get("title") or a.get_text()).strip()
                if query.lower() in text.lower() and "/manga/" in href:
                    results.append({"title": text, "url": href})
        time.sleep(0.8)
        return results

    def get_chapters(self, manga_url):
        """
        return list of {"title":..., "url":...} sorted by appearance
        """
        r = self.session.get(manga_url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        chapters = []
        # common pattern: chapters list links inside .chapter-list or .chapters
        for sel in [".chapters a", ".chapter a", ".post-body a", ".wp-manga-chapter a"]:
            for a in soup.select(sel):
                href = a.get("href")
                title = a.get_text().strip()
                if href and title:
                    chapters.append({"title": title, "url": href})
            if chapters:
                break
        # remove duplicates while preserving order
        seen = set()
        filtered = []
        for c in chapters:
            if c["url"] in seen:
                continue
            seen.add(c["url"])
            filtered.append(c)
        # reverse if they are newest-first and you want reading order oldest-first:
        # filtered.reverse()
        time.sleep(0.6)
        return filtered

    def get_images(self, chapter_url):
        """
        return list of image URLs in reading order
        """
        r = self.session.get(chapter_url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        imgs = []
        # try common containers
        for sel in ["div.page img", ".reader img", ".entry-content img", ".post img", "img"]:
            for img in soup.select(sel):
                src = img.get("data-src") or img.get("src") or img.get("data-original")
                if src and (src.startswith("http") or src.startswith("//")):
                    if src.startswith("//"):
                        src = "https:" + src
                    imgs.append(src)
            if imgs:
                break
        # fallback: look for scripts that contain image arrays (not implemented fully)
        time.sleep(0.5)
        return imgs
      
