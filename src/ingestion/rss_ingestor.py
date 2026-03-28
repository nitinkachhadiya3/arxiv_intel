"""
RSS Feed Ingestor — fetches latest articles from TechCrunch, The Verge, Ars Technica.
Scores them by recency and AI/tech relevance, returns a post-ready topic dict.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import feedparser
import yaml
from pathlib import Path


class RssItem:
    """Backward compatibility class for compiled bytecode."""
    def __init__(self, title: str, summary: str, link: str, source: str, published_ts: Optional[float] = None):
        self.title = title
        self.summary = summary
        self.link = link
        self.source = source
        self.published_ts = published_ts


class RssIngestor:
    """Backward compatibility class for compiled bytecode."""
    def __init__(self, config: Optional[Any] = None):
        self.config = config

    def fetch_all(self) -> List[RssItem]:
        articles = fetch_rss_feeds()
        return [RssItem(a["title"], a["summary"], a["link"], a["source"], a["published_ts"]) for a in articles]



_TECH_KEYWORDS = {
    "ai", "artificial intelligence", "machine learning", "deep learning", "llm",
    "gpt", "openai", "google", "microsoft", "meta", "nvidia", "apple", "amazon",
    "robot", "autonomous", "agent", "agentic", "chip", "semiconductor", "gpu",
    "cloud", "data center", "startup", "funding", "acquisition", "launch",
    "model", "benchmark", "open source", "security", "privacy", "regulation",
    "quantum", "biotech", "neuralink", "spacex", "tesla", "hugging face",
    "transformer", "diffusion", "multimodal", "reasoning", "fine-tuning",
}


def _load_feed_urls() -> List[str]:
    """Load RSS feed URLs from settings.yaml."""
    settings_path = Path("config/settings.yaml")
    if settings_path.exists():
        with open(settings_path) as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("rss", {}).get("feed_urls", [])
    return [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/index",
    ]


def _tech_relevance_score(title: str, summary: str) -> float:
    """Score 0-1 based on how many tech keywords appear."""
    combined = (title + " " + summary).lower()
    hits = sum(1 for kw in _TECH_KEYWORDS if kw in combined)
    return min(1.0, hits / 5.0)


def _recency_score(published_ts: Optional[float]) -> float:
    """Score 0-1 based on how recent the article is (24h window)."""
    if not published_ts:
        return 0.3
    age_hours = (time.time() - published_ts) / 3600
    if age_hours < 1:
        return 1.0
    elif age_hours < 6:
        return 0.85
    elif age_hours < 12:
        return 0.65
    elif age_hours < 24:
        return 0.4
    return 0.1


def fetch_rss_feeds(feed_urls: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Parse all RSS feeds, return articles from last 48h."""
    if feed_urls is None:
        feed_urls = _load_feed_urls()

    articles = []
    cutoff = time.time() - (48 * 3600)  # 48 hours

    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            source_name = feed.feed.get("title", url.split("/")[2])
            for entry in feed.entries[:15]:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = time.mktime(entry.published_parsed)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = time.mktime(entry.updated_parsed)

                if published and published < cutoff:
                    continue

                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                # Clean HTML tags from summary
                import re
                summary = re.sub(r"<[^>]+>", "", summary)[:500]
                link = entry.get("link", "")

                if not title:
                    continue

                articles.append({
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "source": source_name,
                    "published_ts": published,
                })
        except Exception as e:
            print(f"  ⚠ RSS fetch failed for {url}: {e}")
            continue

    return articles


def score_articles(articles: List[Dict]) -> List[Dict]:
    """Score and rank articles by relevance + recency."""
    for a in articles:
        tech = _tech_relevance_score(a["title"], a["summary"])
        recency = _recency_score(a.get("published_ts"))
        a["score"] = (tech * 0.6) + (recency * 0.4)

    return sorted(articles, key=lambda x: x["score"], reverse=True)


def pick_best_rss_topic() -> Optional[Dict[str, Any]]:
    """Fetch, score, and return the top RSS article as a post-ready dict."""
    articles = fetch_rss_feeds()
    if not articles:
        return None

    ranked = score_articles(articles)
    # Filter for minimum tech relevance
    relevant = [a for a in ranked if a["score"] > 0.3]
    if not relevant:
        return None

    best = relevant[0]
    title = best["title"]
    summary = best["summary"]

    # Split summary into slide-sized chunks
    sentences = [s.strip() for s in summary.replace("\n", " ").split(".") if s.strip()]
    slides = []
    slides.append(title)
    for s in sentences[:3]:
        if len(s) > 15:
            slides.append(s + ".")
    while len(slides) < 4:
        slides.append(f"Source: {best['source']}")

    return {
        "topic": title[:80],
        "slides": slides[:4],
        "sources": [{"title": best["source"], "url": best["link"]}],
        "hashtags": "#TechNews #AI #Innovation #FutureOfTech #ArxivIntel",
        "content_source": "rss",
    }
