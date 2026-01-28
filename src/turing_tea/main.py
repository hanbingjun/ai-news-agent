"""
Main entry point for 图灵的下午茶 Agent.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from turing_tea.collector import TuringTeaCollector
from turing_tea.processor import TuringTeaProcessor
from feishu import FeishuNotifier


def main():
    """Run the 图灵的下午茶 news pipeline."""
    load_dotenv()

    print(f"Starting 图灵的下午茶 Agent at {datetime.utcnow().isoformat()}")

    # Step 1: Collect news
    print("\n[1/3] Collecting AI hardware/software news...")
    collector = TuringTeaCollector()
    items = collector.collect_all()

    if not items:
        print("No news items found. Exiting.")
        return

    # Step 2: Process and generate report
    print("\n[2/3] Generating professional analysis...")
    processor = TuringTeaProcessor()
    report = processor.generate_report(items)

    # Save report to file
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f"turing_tea_{today}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved to: {output_path}")

    # Step 3: Send to Feishu
    print("\n[3/3] Sending to Feishu...")
    try:
        notifier = FeishuNotifier()
        success = notifier.send_markdown(f"☕ 图灵的下午茶 - {today}", report)
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
