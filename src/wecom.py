"""
企业微信机器人 webhook 推送模块
"""

import os
import httpx


class WeComNotifier:
    """Send notifications to WeCom (企业微信) via webhook."""

    def __init__(self):
        self.webhook_url = os.getenv("WECOM_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("WECOM_WEBHOOK_URL environment variable is required")

    def send_markdown(self, content: str) -> bool:
        """
        Send a markdown message to WeCom.

        Note: 企业微信 markdown 支持有限，主要支持：
        - 标题：# ## ###
        - 加粗：**text**
        - 链接：[text](url)
        - 引用：> text
        - 颜色：<font color="info/warning/comment">text</font>
        """
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": self._truncate_content(content),
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

            if result.get("errcode") == 0:
                print("Successfully sent to WeCom")
                return True
            else:
                print(f"WeCom API error: {result}")
                return False

        except Exception as e:
            print(f"Error sending to WeCom: {e}")
            return False

    def _truncate_content(self, content: str, max_length: int = 4096) -> str:
        """Truncate content to fit WeCom message limits (4096 bytes)."""
        # 中文字符约3字节，保守估计
        if len(content.encode('utf-8')) <= max_length:
            return content

        # 按字符截断
        truncated = content
        while len(truncated.encode('utf-8')) > max_length - 50:
            truncated = truncated[:-100]

        last_newline = truncated.rfind("\n")
        if last_newline > len(truncated) // 2:
            truncated = truncated[:last_newline]

        return truncated + "\n\n... 内容已截断 ..."

    def send_text(self, text: str) -> bool:
        """Send a simple text message to WeCom."""
        payload = {
            "msgtype": "text",
            "text": {"content": text},
        }

        try:
            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("errcode") == 0
        except Exception as e:
            print(f"Error sending to WeCom: {e}")
            return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    notifier = WeComNotifier()
    notifier.send_text("Test message from AI News Agent")
