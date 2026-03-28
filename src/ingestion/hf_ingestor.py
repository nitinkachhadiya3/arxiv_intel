"""
Hugging Face Ingestor — fetches daily papers, trending models, and trending spaces.
Returns a post-ready topic dict.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests


_HF_PAPERS_URL = "https://huggingface.co/api/daily_papers"
_HF_MODELS_URL = "https://huggingface.co/api/models"
_HF_SPACES_URL = "https://huggingface.co/api/spaces"

_TIMEOUT = 15


def fetch_hf_daily_papers(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch today's top daily papers from HuggingFace."""
    try:
        resp = requests.get(_HF_PAPERS_URL, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data[:limit]:
            paper = item.get("paper", {})
            papers.append({
                "title": item.get("title") or paper.get("title", ""),
                "summary": paper.get("summary", "")[:500],
                "upvotes": paper.get("upvotes", 0),
                "arxiv_id": paper.get("id", ""),
                "url": f"https://huggingface.co/papers/{paper.get('id', '')}",
                "type": "paper",
            })
        return papers
    except Exception as e:
        print(f"  ⚠ HF papers fetch failed: {e}")
        return []


def fetch_hf_trending_models(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch trending models from HuggingFace (sorted by likes in last 7 days)."""
    try:
        resp = requests.get(
            _HF_MODELS_URL,
            params={"sort": "likes7d", "direction": -1, "limit": limit},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        models = []
        for item in data[:limit]:
            model_id = item.get("modelId", item.get("id", ""))
            models.append({
                "title": model_id,
                "summary": item.get("pipeline_tag", "General AI model"),
                "likes": item.get("likes", 0),
                "downloads": item.get("downloads", 0),
                "url": f"https://huggingface.co/{model_id}",
                "type": "model",
            })
        return models
    except Exception as e:
        print(f"  ⚠ HF models fetch failed: {e}")
        return []


def fetch_hf_trending_spaces(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch trending spaces from HuggingFace."""
    try:
        resp = requests.get(
            _HF_SPACES_URL,
            params={"sort": "likes7d", "direction": -1, "limit": limit},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        spaces = []
        for item in data[:limit]:
            space_id = item.get("id", "")
            spaces.append({
                "title": space_id,
                "summary": item.get("cardData", {}).get("short_description", "")
                           or item.get("sdk", "Interactive AI demo"),
                "likes": item.get("likes", 0),
                "url": f"https://huggingface.co/spaces/{space_id}",
                "type": "space",
            })
        return spaces
    except Exception as e:
        print(f"  ⚠ HF spaces fetch failed: {e}")
        return []


def _paper_to_post(paper: Dict) -> Dict[str, Any]:
    """Convert an HF paper to a post-ready dict."""
    title = paper["title"]
    summary = paper["summary"]

    # Split summary into sentence-sized slides
    sentences = [s.strip() for s in summary.replace("\n", " ").split(".") if len(s.strip()) > 20]
    slides = [title]
    for s in sentences[:3]:
        slides.append(s[:120] + ("..." if len(s) > 120 else "."))
    while len(slides) < 4:
        slides.append(f"Read the full paper on HuggingFace and arXiv.")

    return {
        "topic": title[:80],
        "slides": slides[:4],
        "sources": [{"title": "Hugging Face Daily Papers", "url": paper["url"]}],
        "hashtags": "#AI #Research #MachineLearning #HuggingFace #ArxivIntel",
        "content_source": "hf_paper",
    }


def _model_to_post(model: Dict) -> Dict[str, Any]:
    """Convert an HF trending model to a post-ready dict."""
    model_id = model["title"]
    # Clean model name for headline
    name = model_id.split("/")[-1] if "/" in model_id else model_id
    org = model_id.split("/")[0] if "/" in model_id else "Community"

    headline = f"{name} Is Now the Most Popular AI Model on HuggingFace"
    if len(headline) > 80:
        headline = f"{name}: Trending on HuggingFace"[:80]

    slides = [
        headline,
        f"{name} by {org} is trending with {model['likes']:,} likes on HuggingFace.",
        f"Task: {model['summary']}. Downloaded {model['downloads']:,} times.",
        f"Open-source AI models are reshaping the industry — accessible to everyone.",
    ]

    return {
        "topic": headline,
        "slides": slides,
        "sources": [{"title": f"HuggingFace: {model_id}", "url": model["url"]}],
        "hashtags": "#AI #OpenSource #HuggingFace #MachineLearning #TechNews",
        "content_source": "hf_model",
    }


def _space_to_post(space: Dict) -> Dict[str, Any]:
    """Convert an HF trending space to a post-ready dict."""
    space_id = space["title"]
    name = space_id.split("/")[-1] if "/" in space_id else space_id
    org = space_id.split("/")[0] if "/" in space_id else "Community"

    headline = f"{name}: The AI Demo Everyone Is Trying Right Now"
    if len(headline) > 80:
        headline = f"{name} — Trending AI Demo"[:80]

    slides = [
        headline,
        f"{name} by {org} is trending with {space['likes']:,} likes on HuggingFace Spaces.",
        f"Description: {space['summary'][:120]}.",
        f"Try it yourself — AI demos are making cutting-edge research accessible.",
    ]

    return {
        "topic": headline,
        "slides": slides,
        "sources": [{"title": f"HuggingFace Space: {space_id}", "url": space["url"]}],
        "hashtags": "#AI #HuggingFace #Demo #MachineLearning #Innovation",
        "content_source": "hf_space",
    }


def pick_best_hf_topic(source_subtype: str = "paper") -> Optional[Dict[str, Any]]:
    """
    Pick the best HF topic based on the requested subtype.
    source_subtype: "paper", "model", or "space"
    """
    if source_subtype == "paper":
        papers = fetch_hf_daily_papers()
        if papers:
            # Pick the one with most upvotes
            best = max(papers, key=lambda p: p.get("upvotes", 0))
            return _paper_to_post(best)

    elif source_subtype == "model":
        models = fetch_hf_trending_models()
        if models:
            best = models[0]  # Already sorted by likes7d
            return _model_to_post(best)

    elif source_subtype == "space":
        spaces = fetch_hf_trending_spaces()
        if spaces:
            best = spaces[0]
            return _space_to_post(best)

    # Fallback: try papers
    papers = fetch_hf_daily_papers()
    if papers:
        best = max(papers, key=lambda p: p.get("upvotes", 0))
        return _paper_to_post(best)

    return None
