"""
Processor for 图灵的下午茶 - 专业分析生成
"""

import os
from datetime import datetime
import anthropic
from .collector import TechNewsItem
from .config import OUTPUT_NEWS_COUNT


class TuringTeaProcessor:
    """Generate professional AI hardware/software analysis."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_report(self, items: list[TechNewsItem]) -> str:
        """Generate the 图灵的下午茶 report."""
        if not items:
            return self._empty_report()

        # Step 1: 让 Claude 从候选新闻中筛选最有工程价值的 3 条
        selected_items = self._select_top_news(items)

        # Step 2: 为每条生成深度分析
        analyses = []
        for i, item in enumerate(selected_items, 1):
            print(f"Analyzing item {i}/{len(selected_items)}...")
            analysis = self._generate_analysis(item)
            analyses.append((item, analysis))

        # Step 3: 构建最终报告
        report = self._build_report(analyses)
        return report

    def _select_top_news(self, items: list[TechNewsItem]) -> list[TechNewsItem]:
        """Use Claude to select the most valuable news items."""
        # 准备候选列表
        candidates = ""
        for i, item in enumerate(items[:15], 1):  # 最多考虑 15 条
            tech_mark = "[技术社区]" if item.is_tech_source else ""
            candidates += f"{i}. {tech_mark} [{item.category}] {item.title}\n"
            candidates += f"   来源: {item.source_domain}\n"
            candidates += f"   内容: {item.content[:300]}...\n\n"

        prompt = f"""你是《图灵的下午茶》栏目的编辑，需要筛选兼具"硬件性能"与"算法突破"的深度动态。

请从以下候选新闻中，选出最具"工程参考价值"的 {OUTPUT_NEWS_COUNT} 条。

筛选标准：
1. 优先选择展示"软硬协同"的新闻（如：模型优化如何降低硬件需求）
2. 必须包含至少 1 条来自技术社区的新闻
3. 关注具体技术指标：TFLOPS、显存占用、推理成本等

候选新闻：
{candidates}

请只返回你选择的新闻编号，用逗号分隔，如：3,7,12
不要返回其他内容。"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}],
            )
            selected_nums = response.content[0].text.strip()
            indices = [int(n.strip()) - 1 for n in selected_nums.split(",")]
            return [items[i] for i in indices if 0 <= i < len(items)][:OUTPUT_NEWS_COUNT]
        except Exception as e:
            print(f"Error selecting news: {e}")
            # Fallback: 返回前 3 条
            return items[:OUTPUT_NEWS_COUNT]

    def _generate_analysis(self, item: TechNewsItem) -> dict:
        """Generate Ada-style professional analysis for a news item."""
        prompt = f"""你是"Ada"，一位具备系统工程师视角的 AI 行业分析师，语气专业且犀利。

请为以下新闻生成分析：

标题：{item.title}
来源：{item.source_domain}
内容：{item.content[:1000]}

请生成：
1. **新标题**：重新拟一个标题，需同时涵盖软件进展与底层硬件支撑（如有）
2. **深度综述**：150字左右，需提到具体型号、参数或算法逻辑。例如：模型对显存的占用、算力需求、量化技术等
3. **值得关注的原因**：从 IT 工程师视角，该进展对企业级硬件采购计划或国产化替代方案有何实际指导意义？

请用以下 JSON 格式返回（确保是合法 JSON）：
{{"title": "新标题", "summary": "深度综述内容", "insight": "值得关注的原因"}}"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            import json
            result = response.content[0].text.strip()
            # 尝试解析 JSON
            return json.loads(result)
        except Exception as e:
            print(f"Error generating analysis: {e}")
            return {
                "title": item.title,
                "summary": item.content[:150],
                "insight": "暂无分析"
            }

    def _build_report(self, analyses: list[tuple[TechNewsItem, dict]]) -> str:
        """Build the final markdown report."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        report = f"""## ☕ 图灵的下午茶：AI 软硬协同 & 推理前沿 [{today}]

"""
        for i, (item, analysis) in enumerate(analyses, 1):
            title = analysis.get("title", item.title)
            summary = analysis.get("summary", "")
            insight = analysis.get("insight", "")

            report += f"""**{i}. {title}**
- 🔍 **深度综述**: {summary}
- 💡 **值得关注的原因**: {insight}
- 🔗 [原文链接]({item.url})

"""
        return report

    def _empty_report(self) -> str:
        """Return empty report."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return f"## ☕ 图灵的下午茶 [{today}]\n\n今日暂无符合条件的软硬协同动态。"


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    from .collector import TuringTeaCollector

    collector = TuringTeaCollector()
    items = collector.collect_all()

    processor = TuringTeaProcessor()
    report = processor.generate_report(items)
    print(report)
