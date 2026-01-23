"""
Processor module for summarizing news using Claude API.
"""

import os
from datetime import datetime
import anthropic
from collector import NewsItem


class NewsProcessor:
    """Process and summarize news items using Claude."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        self.client = anthropic.Anthropic(api_key=api_key)

    def summarize_item(self, item: NewsItem) -> str:
        """Generate a brief summary for a single news item."""
        prompt = f"""请用中文为以下内容生成一句话摘要（不超过50字）：

标题：{item.title}
内容：{item.content[:500]}

只输出摘要，不要其他内容。"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"Error summarizing: {e}")
            return ""

    def generate_daily_report(self, items: list[NewsItem]) -> str:
        """Generate a complete daily report in Markdown format."""
        if not items:
            return "# AI 资讯日报\n\n今日暂无相关资讯。"

        # Prepare items text for summary
        items_text = ""
        for i, item in enumerate(items[:20], 1):  # Top 20 items
            items_text += f"{i}. [{item.source}] {item.title}\n"
            if item.content:
                items_text += f"   {item.content[:200]}...\n"

        # Generate overall summary
        summary_prompt = f"""请根据以下 AI 领域资讯列表，用中文生成一段今日热点概述（100-150字），突出最重要的 2-3 个话题：

{items_text}

只输出概述，不要标题。"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                messages=[{"role": "user", "content": summary_prompt}],
            )
            overview = response.content[0].text.strip()
        except Exception as e:
            print(f"Error generating overview: {e}")
            overview = "暂无概述。"

        # Build Markdown report
        report = self._build_markdown_report(items, overview)
        return report

    def _build_markdown_report(self, items: list[NewsItem], overview: str) -> str:
        """Build the final Markdown report."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        report = f"""# AI 资讯日报 - {today}

## 今日概述

{overview}

---

## 热门资讯（按热度排序）

"""
        # Group by source
        reddit_items = [i for i in items if i.source == "reddit"]
        twitter_items = [i for i in items if i.source == "twitter"]

        if reddit_items:
            report += "### Reddit\n\n"
            for i, item in enumerate(reddit_items[:10], 1):
                subreddit = f"r/{item.subreddit}" if item.subreddit else "Reddit"
                report += f"{i}. **[{subreddit}]** [{item.title}]({item.url})\n"
                report += f"   - 热度: {item.score}\n"
                if item.content:
                    summary = item.content[:100].replace("\n", " ")
                    report += f"   - 摘要: {summary}...\n"
                report += "\n"

        if twitter_items:
            # Separate influencer tweets from general tweets
            influencer_items = [i for i in twitter_items if i.author]
            general_twitter = [i for i in twitter_items if not i.author]

            if influencer_items:
                report += "### AI 大神动态\n\n"
                for i, item in enumerate(influencer_items[:10], 1):
                    author_info = f"**@{item.author}** ({item.author_name})"
                    report += f"{i}. {author_info}\n"
                    report += f"   - [{item.title}]({item.url})\n"
                    if item.content:
                        summary = item.content[:100].replace("\n", " ")
                        report += f"   - {summary}...\n"
                    report += "\n"

            if general_twitter:
                report += "### Twitter/X 热门\n\n"
                for i, item in enumerate(general_twitter[:10], 1):
                    report += f"{i}. [{item.title}]({item.url})\n"
                    if item.content:
                        summary = item.content[:100].replace("\n", " ")
                        report += f"   - 摘要: {summary}...\n"
                    report += "\n"

        report += f"""---

*Generated at {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC*
"""
        return report


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Test with sample data
    sample_items = [
        NewsItem(
            title="New breakthrough in AI Agents",
            url="https://example.com/1",
            content="Researchers have developed a new approach...",
            source="reddit",
            score=1500,
            published_at=datetime.utcnow(),
            subreddit="MachineLearning",
        ),
    ]

    processor = NewsProcessor()
    report = processor.generate_daily_report(sample_items)
    print(report)
