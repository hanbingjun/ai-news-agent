"""
Main entry point for AI News Agent.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from collector import NewsCollector
from processor import NewsProcessor
from feishu import FeishuNotifier


def main():
    """Run the complete news collection and notification pipeline."""
    load_dotenv()

    print(f"Starting AI News Agent at {datetime.utcnow().isoformat()}")

    # Step 1: Collect news
    print("\n[1/3] Collecting news...")
    collector = NewsCollector()
    items = collector.collect_all()

    if not items:
        print("No news items found. Exiting.")
        return

    # Step 2: Process and generate report
    print("\n[2/3] Generating report...")
    processor = NewsProcessor()
    report = processor.generate_daily_report(items)

    # Save report to file
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f"report_{today}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved to: {output_path}")

    # Step 3: Send to Feishu
    print("\n[3/3] Sending to Feishu...")
    try:
        notifier = FeishuNotifier()
        success = notifier.send_markdown(f"AI 资讯日报 - {today}", report)
        if success:
            print("Successfully sent to Feishu!")
        else:
            print("Failed to send to Feishu")
            sys.exit(1)
    except ValueError as e:
        print(f"Feishu not configured: {e}")
        print("Skipping Feishu notification")

    print("\nDone!")


if __name__ == "__main__":
    main()
