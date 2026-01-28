"""
Collector for 图灵的下午茶 - AI 软硬协同新闻采集
"""

import os
from datetime import datetime
from dataclasses import dataclass
from tavily import TavilyClient
from .config import (
    HARDWARE_KEYWORDS,
    SOFTWARE_KEYWORDS,
    TECH_DOMAINS,
    NEWS_DOMAINS,
    MAX_RESULTS_PER_KEYWORD,
)


@dataclass
class TechNewsItem:
    """Represents a tech news item with hardware/software context."""
    title: str
    url: str
    content: str
    source_domain: str
    relevance_score: float
    is_tech_source: bool  # 是否来自专业技术社区
    category: str  # 'hardware' or 'software'


class TuringTeaCollector:
    """Collect AI hardware/software synergy news."""

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is required")
        self.client = TavilyClient(api_key=api_key)

    def collect_all(self) -> list[TechNewsItem]:
        """Collect news from both hardware and software dimensions."""
        all_items = []

        # 1. 收集硬件相关新闻
        print("Collecting hardware news...")
        hardware_items = self._search_category(HARDWARE_KEYWORDS, "hardware")
        all_items.extend(hardware_items)
        print(f"  Found {len(hardware_items)} hardware items")

        # 2. 收集软件相关新闻
        print("Collecting software news...")
        software_items = self._search_category(SOFTWARE_KEYWORDS, "software")
        all_items.extend(software_items)
        print(f"  Found {len(software_items)} software items")

        # 3. 搜索专业技术社区
        print("Collecting from tech communities...")
        tech_items = self._search_tech_sources()
        all_items.extend(tech_items)
        print(f"  Found {len(tech_items)} tech community items")

        # 去重
        seen_urls = set()
        unique_items = []
        for item in all_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)

        # 按相关性排序，优先技术社区来源
        unique_items.sort(
            key=lambda x: (x.is_tech_source, x.relevance_score),
            reverse=True
        )

        print(f"Total unique items: {len(unique_items)}")
        return unique_items

    def _search_category(self, keywords: list[str], category: str) -> list[TechNewsItem]:
        """Search for news in a specific category."""
        items = []
        all_domains = TECH_DOMAINS + NEWS_DOMAINS

        for keyword in keywords:
            try:
                results = self.client.search(
                    query=keyword,
                    search_depth="advanced",
                    include_domains=all_domains,
                    max_results=MAX_RESULTS_PER_KEYWORD,
                    include_raw_content=False,
                )

                for result in results.get("results", []):
                    url = result.get("url", "")
                    domain = self._extract_domain(url)
                    is_tech = any(td in url for td in TECH_DOMAINS)

                    item = TechNewsItem(
                        title=result.get("title", ""),
                        url=url,
                        content=result.get("content", ""),
                        source_domain=domain,
                        relevance_score=result.get("score", 0),
                        is_tech_source=is_tech,
                        category=category,
                    )
                    items.append(item)

            except Exception as e:
                print(f"  Error searching '{keyword}': {e}")

        return items

    def _search_tech_sources(self) -> list[TechNewsItem]:
        """Search specifically in tech communities for AI chip/model news."""
        items = []

        # 综合搜索词
        synergy_queries = [
            "GPU AI inference optimization",
            "LLM hardware requirements",
            "AI chip benchmark 2024",
            "transformer memory optimization",
        ]

        for query in synergy_queries:
            try:
                results = self.client.search(
                    query=query,
                    search_depth="advanced",
                    include_domains=TECH_DOMAINS,
                    max_results=MAX_RESULTS_PER_KEYWORD,
                    include_raw_content=False,
                )

                for result in results.get("results", []):
                    url = result.get("url", "")
                    item = TechNewsItem(
                        title=result.get("title", ""),
                        url=url,
                        content=result.get("content", ""),
                        source_domain=self._extract_domain(url),
                        relevance_score=result.get("score", 0) + 0.2,  # Boost
                        is_tech_source=True,
                        category="synergy",
                    )
                    items.append(item)

            except Exception as e:
                print(f"  Error in tech search: {e}")

        return items

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return ""


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    collector = TuringTeaCollector()
    items = collector.collect_all()

    print("\n=== Top Items ===")
    for i, item in enumerate(items[:10], 1):
        tech_mark = "🔧" if item.is_tech_source else ""
        print(f"{i}. [{item.category}] {tech_mark} {item.title}")
        print(f"   {item.source_domain} | Score: {item.relevance_score:.2f}")
