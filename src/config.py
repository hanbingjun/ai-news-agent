"""Configuration for AI News Agent."""

# Search keywords for general AI news
KEYWORDS = [
    "AI Agent",
    "Large Language Models",
    "LLM",
    "World Models",
    "GPT-5",
    "Claude",
    "Gemini",
    "AI breakthrough",
]

# Reddit subreddits to monitor
SUBREDDITS = [
    "MachineLearning",
    "LocalLLaMA",
]

# AI thought leaders on Twitter/X to track
TWITTER_INFLUENCERS = [
    ("AndrewYNg", "吴恩达 - Landing AI/Coursera 创始人"),
    ("ylecun", "Yann LeCun - Meta AI 首席科学家"),
    ("fchollet", "François Chollet - Keras 创始人"),
    ("demaboranashis", "Demis Hassabis - DeepMind CEO"),
    ("karpathy", "Andrej Karpathy - 前 Tesla AI 负责人"),
    ("sama", "Sam Altman - OpenAI CEO"),
    ("tunguz", "Bojan Tunguz - Kaggle Grandmaster"),
]

# Number of results per search
MAX_RESULTS_PER_KEYWORD = 5
MAX_RESULTS_PER_INFLUENCER = 3

# Time range for search (in days)
SEARCH_DAYS = 1
