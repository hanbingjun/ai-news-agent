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
        """Generate a brief Chinese summary for a single news item."""
        prompt = f"""请用中文为以下内容生成一句话摘要（不超过50字）：

标题：{item.title}
内容：{item.content[:500] if item.content else "无"}

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
            return "# AI 新闻日报\n\n今日暂无相关资讯。"

        # Separate items by type
        twitter_items = [i for i in items if i.source == "twitter"]
        reddit_items = [i for i in items if i.source == "reddit"]

        influencer_items = [i for i in twitter_items if i.author][:5]
        general_twitter = [i for i in twitter_items if not i.author][:5]
        reddit_items = reddit_items[:5]

        # Generate summaries for top items
        print("Generating Chinese summaries...")
        all_top_items = influencer_items + general_twitter + reddit_items
        summaries = {}
        for item in all_top_items:
            summary = self.summarize_item(item)
            summaries[item.url] = summary

        # Build report
        report = self._build_markdown_report(
            influencer_items, general_twitter, reddit_items, summaries
        )
        return report

    def _build_markdown_report(
        self,
        influencer_items: list[NewsItem],
        general_twitter: list[NewsItem],
        reddit_items: list[NewsItem],
        summaries: dict[str, str],
    ) -> str:
        """Build the final Markdown report."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        report = f"""# AI 新闻日报 - {today}

"""
        if influencer_items:
            report += "## AI 大神动态\n\n"
            for i, item in enumerate(influencer_items, 1):
                summary = summaries.get(item.url, "")
                report += f"{i}. **@{item.author}** ({item.author_name})\n"
                report += f"   [{item.title}]({item.url})\n"
                if summary:
                    report += f"   摘要：{summary}\n"
                report += "\n"

        if general_twitter:
            report += "## Twitter 热门\n\n"
            for i, item in enumerate(general_twitter, 1):
                summary = summaries.get(item.url, "")
                report += f"{i}. [{item.title}]({item.url})\n"
                if summary:
                    report += f"   摘要：{summary}\n"
                report += "\n"

        if reddit_items:
            report += "## Reddit 热门\n\n"
            for i, item in enumerate(reddit_items, 1):
                summary = summaries.get(item.url, "")
                subreddit = f"r/{item.subreddit}" if item.subreddit else ""
                report += f"{i}. **[{subreddit}]** [{item.title}]({item.url})\n"
                if summary:
                    report += f"   摘要：{summary}\n"
                report += "\n"

        return report


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    from collector import NewsCollector
    collector = NewsCollector()
    items = collector.collect_all()

    processor = NewsProcessor()
    report = processor.generate_daily_report(items)
    print(report)
