"""Configuration for 图灵的下午茶 Agent."""

# 算力基座 (Hardware) 关键词
HARDWARE_KEYWORDS = [
    # 国际
    "NVIDIA Blackwell",
    "NVIDIA B200",
    "NVIDIA GB200",
    "AMD MI300",
    "AMD MI325X",
    "HBM3e",
    # 国内信创
    "华为昇腾",
    "Huawei Ascend 910",
    "海光 Hygon",
    "寒武纪 Cambricon",
    # 技术指标
    "TFLOPS benchmark",
    "Memory Wall GPU",
    "GPU memory bandwidth",
]

# 逻辑进化 (Software & Skills) 关键词
SOFTWARE_KEYWORDS = [
    # OpenAI 体系
    "OpenAI o1",
    "OpenAI o3",
    "System 2 Thinking AI",
    "Chain-of-Thought reasoning",
    # 智能体与模型
    "AI Agent autonomous",
    "World Models AI",
    "Physical AI robotics",
    "embodied AI",
]

# 专业技术社区
TECH_DOMAINS = [
    "huggingface.co",
    "github.com",
    "arxiv.org",
    "semianalysis.com",
    "anandtech.com",
    "tomshardware.com",
]

# 通用 AI 新闻源
NEWS_DOMAINS = [
    "twitter.com",
    "x.com",
    "reddit.com",
    "techcrunch.com",
    "theverge.com",
    "venturebeat.com",
]

# 每个关键词搜索结果数
MAX_RESULTS_PER_KEYWORD = 3

# 最终输出条数
OUTPUT_NEWS_COUNT = 3
