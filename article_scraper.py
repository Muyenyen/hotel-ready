import requests
import trafilatura

def scrape_article(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        return extracted
    except Exception as e:
        return f"[Scraper Error] {e}"