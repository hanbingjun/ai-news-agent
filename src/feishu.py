"""
Feishu (Lark) webhook notification module.
"""

import os
import httpx


class FeishuNotifier:
    """Send notifications to Feishu via webhook."""

    def __init__(self):
        self.webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("FEISHU_WEBHOOK_URL environment variable is required")

    def send_markdown(self, title: str, content: str) -> bool:
        """
        Send a markdown message to Feishu.

        Note: Feishu webhook has message size limits, so we may need to truncate.
        """
        # Feishu uses a specific format for rich text messages
        # For simplicity, we'll use the text card format
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title,
                    },
                    "template": "blue",
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": self._truncate_content(content),
                    }
                ],
            },
        }

        try:
            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print("Successfully sent to Feishu")
                return True
            else:
                print(f"Feishu API error: {result}")
                return False

        except Exception as e:
            print(f"Error sending to Feishu: {e}")
            return False

    def _truncate_content(self, content: str, max_length: int = 4000) -> str:
        """Truncate content to fit Feishu message limits."""
        if len(content) <= max_length:
            return content

        # Truncate and add notice
        truncated = content[: max_length - 50]
        # Try to cut at a line break
        last_newline = truncated.rfind("\n")
        if last_newline > max_length // 2:
            truncated = truncated[:last_newline]

        return truncated + "\n\n*... 内容过长，已截断 ...*"

    def send_simple_text(self, text: str) -> bool:
        """Send a simple text message to Feishu."""
        payload = {
            "msg_type": "text",
            "content": {"text": text},
        }

        try:
            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending to Feishu: {e}")
            return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    notifier = FeishuNotifier()
    notifier.send_simple_text("Test message from AI News Agent")
