"""
Collector module for fetching AI news from Reddit and Twitter/X.
Uses Tavily Search API and Reddit API (PRAW).
"""

import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from tavily import TavilyClient
import praw
from config import KEYWORDS, SUBREDDITS, SEARCH_DOMAINS, MAX_RESULTS_PER_SEARCH, SEARCH_DAYS


@dataclass
class NewsItem:
    """Represents a single news item."""
    title: str
    url: str
    content: str
    source: str  # 'reddit' or 'twitter'
    score: int  # upvotes/likes for ranking
    published_at: datetime | None
    subreddit: str | None = None


class TavilyCollector:
    """Collect news using Tavily Search API."""

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is required")
        self.client = TavilyClient(api_key=api_key)

    def search(self, keywords: list[str], domains: list[str]) -> list[NewsItem]:
        """Search for news items using Tavily API."""
        items = []

        for keyword in keywords:
            try:
                results = self.client.search(
                    query=keyword,
                    search_depth="advanced",
                    include_domains=domains,
                    max_results=MAX_RESULTS_PER_SEARCH,
                    include_raw_content=False,
                )

                for result in results.get("results", []):
                    source = self._detect_source(result.get("url", ""))
                    item = NewsItem(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        content=result.get("content", ""),
                        source=source,
                        score=result.get("score", 0) * 100,  # Tavily relevance score
                        published_at=None,
                        subreddit=self._extract_subreddit(result.get("url", "")),
                    )
                    items.append(item)
            except Exception as e:
                print(f"Error searching for '{keyword}': {e}")

        return items

    def _detect_source(self, url: str) -> str:
        """Detect source from URL."""
        if "reddit.com" in url:
            return "reddit"
        elif "twitter.com" in url or "x.com" in url:
            return "twitter"
        return "other"

    def _extract_subreddit(self, url: str) -> str | None:
        """Extract subreddit name from Reddit URL."""
        if "reddit.com/r/" in url:
            parts = url.split("/r/")
            if len(parts) > 1:
                return parts[1].split("/")[0]
        return None


class RedditCollector:
    """Collect news directly from Reddit using PRAW for accurate scores."""

    def __init__(self):
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")

        if not client_id or not client_secret:
            self.reddit = None
            print("Warning: Reddit API credentials not set, using Tavily only")
            return

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="AI-News-Agent/1.0",
        )

    def collect(self, subreddits: list[str], keywords: list[str]) -> list[NewsItem]:
        """Collect hot posts from specified subreddits."""
        if not self.reddit:
            return []

        items = []
        cutoff_time = datetime.utcnow() - timedelta(days=SEARCH_DAYS)

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                for post in subreddit.hot(limit=50):
                    # Check if post is within time range
                    post_time = datetime.utcfromtimestamp(post.created_utc)
                    if post_time < cutoff_time:
                        continue

                    # Check if post matches any keyword
                    title_lower = post.title.lower()
                    selftext_lower = (post.selftext or "").lower()

                    matches_keyword = any(
                        kw.lower() in title_lower or kw.lower() in selftext_lower
                        for kw in keywords
                    )

                    if not matches_keyword:
                        continue

                    item = NewsItem(
                        title=post.title,
                        url=f"https://reddit.com{post.permalink}",
                        content=post.selftext[:500] if post.selftext else "",
                        source="reddit",
                        score=post.score,
                        published_at=post_time,
                        subreddit=subreddit_name,
                    )
                    items.append(item)

            except Exception as e:
                print(f"Error collecting from r/{subreddit_name}: {e}")

        return items


class NewsCollector:
    """Main collector that combines all sources."""

    def __init__(self):
        self.tavily = TavilyCollector()
        self.reddit = RedditCollector()

    def collect_all(self) -> list[NewsItem]:
        """Collect news from all sources and deduplicate."""
        all_items = []

        # Collect from Tavily (Twitter/X content)
        twitter_domains = ["twitter.com", "x.com"]
        tavily_items = self.tavily.search(KEYWORDS, twitter_domains)
        all_items.extend(tavily_items)
        print(f"Collected {len(tavily_items)} items from Tavily (Twitter/X)")

        # Collect from Reddit directly (more accurate scores)
        reddit_items = self.reddit.collect(SUBREDDITS, KEYWORDS)
        all_items.extend(reddit_items)
        print(f"Collected {len(reddit_items)} items from Reddit API")

        # If Reddit API not available, use Tavily for Reddit too
        if not reddit_items:
            reddit_domains = ["reddit.com"]
            tavily_reddit = self.tavily.search(KEYWORDS, reddit_domains)
            all_items.extend(tavily_reddit)
            print(f"Collected {len(tavily_reddit)} Reddit items from Tavily (fallback)")

        # Deduplicate by URL
        seen_urls = set()
        unique_items = []
        for item in all_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)

        # Sort by score (descending)
        unique_items.sort(key=lambda x: x.score, reverse=True)

        print(f"Total unique items: {len(unique_items)}")
        return unique_items


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    collector = NewsCollector()
    items = collector.collect_all()

    for i, item in enumerate(items[:10], 1):
        print(f"\n{i}. [{item.source}] {item.title}")
        print(f"   Score: {item.score} | URL: {item.url}")
