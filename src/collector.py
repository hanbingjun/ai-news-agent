"""
Collector module for fetching AI news from Reddit and Twitter/X.
Uses Tavily Search API and Reddit API (PRAW).
"""

import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from tavily import TavilyClient
import praw
from config import (
    KEYWORDS,
    SUBREDDITS,
    TWITTER_INFLUENCERS,
    MAX_RESULTS_PER_KEYWORD,
    MAX_RESULTS_PER_INFLUENCER,
    SEARCH_DAYS,
)


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
    author: str | None = None  # Twitter username
    author_name: str | None = None  # Display name (e.g., "吴恩达")


class TavilyCollector:
    """Collect news using Tavily Search API."""

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is required")
        self.client = TavilyClient(api_key=api_key)

    def search_keywords(self, keywords: list[str], domains: list[str]) -> list[NewsItem]:
        """Search for news items by keywords."""
        items = []

        for keyword in keywords:
            try:
                results = self.client.search(
                    query=f"{keyword} AI",
                    search_depth="advanced",
                    include_domains=domains,
                    max_results=MAX_RESULTS_PER_KEYWORD,
                    include_raw_content=False,
                )

                for result in results.get("results", []):
                    source = self._detect_source(result.get("url", ""))
                    item = NewsItem(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        content=result.get("content", ""),
                        source=source,
                        score=int(result.get("score", 0) * 100),
                        published_at=None,
                        subreddit=self._extract_subreddit(result.get("url", "")),
                    )
                    items.append(item)
            except Exception as e:
                print(f"Error searching for '{keyword}': {e}")

        return items

    def search_influencers(self, influencers: list[tuple[str, str]]) -> list[NewsItem]:
        """Search for tweets from specific AI influencers."""
        items = []

        for username, display_name in influencers:
            try:
                # Search for recent tweets from this user
                results = self.client.search(
                    query=f"from:{username} AI OR LLM OR model",
                    search_depth="advanced",
                    include_domains=["twitter.com", "x.com"],
                    max_results=MAX_RESULTS_PER_INFLUENCER,
                    include_raw_content=False,
                )

                for result in results.get("results", []):
                    item = NewsItem(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        content=result.get("content", ""),
                        source="twitter",
                        score=int(result.get("score", 0) * 100) + 50,  # Boost influencer content
                        published_at=None,
                        author=username,
                        author_name=display_name,
                    )
                    items.append(item)

                print(f"  - @{username}: {len(results.get('results', []))} items")

            except Exception as e:
                print(f"Error searching for @{username}: {e}")

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
                    post_time = datetime.utcfromtimestamp(post.created_utc)
                    if post_time < cutoff_time:
                        continue

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

        # 1. Collect from Twitter influencers
        print("Collecting from AI influencers...")
        influencer_items = self.tavily.search_influencers(TWITTER_INFLUENCERS)
        all_items.extend(influencer_items)
        print(f"Collected {len(influencer_items)} items from influencers")

        # 2. Collect general AI news from Twitter
        print("Collecting general AI news from Twitter...")
        twitter_domains = ["twitter.com", "x.com"]
        twitter_items = self.tavily.search_keywords(KEYWORDS, twitter_domains)
        all_items.extend(twitter_items)
        print(f"Collected {len(twitter_items)} general Twitter items")

        # 3. Collect from Reddit directly (more accurate scores)
        print("Collecting from Reddit...")
        reddit_items = self.reddit.collect(SUBREDDITS, KEYWORDS)
        all_items.extend(reddit_items)
        print(f"Collected {len(reddit_items)} items from Reddit API")

        # 4. If Reddit API not available, use Tavily for Reddit
        if not reddit_items:
            reddit_domains = ["reddit.com"]
            tavily_reddit = self.tavily.search_keywords(KEYWORDS, reddit_domains)
            all_items.extend(tavily_reddit)
            print(f"Collected {len(tavily_reddit)} Reddit items from Tavily (fallback)")

        # Deduplicate by URL
        seen_urls = set()
        unique_items = []
        for item in all_items:
            normalized_url = item.url.replace("x.com", "twitter.com")
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
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

    print("\n=== Top 10 Items ===")
    for i, item in enumerate(items[:10], 1):
        author_info = f" (@{item.author})" if item.author else ""
        print(f"\n{i}. [{item.source}]{author_info} {item.title}")
        print(f"   Score: {item.score} | URL: {item.url}")
