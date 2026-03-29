RSS_FEEDS = [
    {
        "name": "The Batch (DeepLearning.AI)",
        "url": "https://www.deeplearning.ai/the-batch/feed/"
    },
    {
        "name": "Lilian Weng's Blog",
        "url": "https://lilianweng.github.io/index.xml"
    },
    {
        "name": "Andrej Karpathy's Blog",
        "url": "https://karpathy.github.io/feed.xml"
    },
    {
        "name": "Import AI Newsletter",
        "url": "https://importai.substack.com/feed"
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml"
    },
    {
        "name": "Berkeley AI Research (BAIR) Blog",
        "url": "https://bair.berkeley.edu/blog/feed.xml"
    },
    {
        "name": "r/LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA/.rss"
    },
    {
        "name": "Dwarkesh Podcast",
        "url": "https://www.dwarkeshpatel.com/feed"
    },
    {
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml"
    },
    {
            "name": "Google Research",
            "url": "https://research.google/blog/rss"
    },
    {
            "name": "AWS ML Blog",
            "url": "https://aws.amazon.com/blogs/machine-learning/feed/"
    },
    {
            "name": "CMU ML Blog",
            "url": "https://blog.ml.cmu.edu/feed"
    },
]

ARXIV_FEEDS = [
    "https://rss.arxiv.org/rss/cs.AI",
    "https://rss.arxiv.org/rss/cs.LG",
    "https://rss.arxiv.org/rss/cs.CL",
    "https://rss.arxiv.org/rss/stat.ML",
]

FOUNDATIONAL_SOURCES = [
    # canonical transformer / attention papers
    {"url": "https://arxiv.org/abs/1706.03762", "title": "Attention Is All You Need", "source": "Arxiv", "date": "2017-06-12"},
    {"url": "https://arxiv.org/abs/2005.14165", "title": "Language Models are Few-Shot Learners (GPT-3)", "source": "Arxiv", "date": "2020-05-28"},
    {"url": "https://arxiv.org/abs/2203.02155", "title": "InstructGPT: Training language models to follow instructions", "source": "Arxiv", "date": "2022-03-04"},
    {"url": "https://arxiv.org/abs/2307.09288", "title": "Llama 2: Open Foundation and Fine-Tuned Chat Models", "source": "Arxiv", "date": "2023-07-18"},

    # RL / RLHF foundations
    {"url": "https://arxiv.org/abs/1707.06347", "title": "Proximal Policy Optimization Algorithms", "source": "Arxiv", "date": "2017-07-20"},
    {"url": "https://arxiv.org/abs/1706.03741", "title": "Deep Reinforcement Learning from Human Preferences", "source": "Arxiv", "date": "2017-06-12"},

    # inference efficiency
    {"url": "https://arxiv.org/abs/2211.17192", "title": "Efficient Streaming Language Models with Attention Sinks", "source": "Arxiv", "date": "2023-09-21"},
    {"url": "https://arxiv.org/abs/2305.13048", "title": "QLoRA: Efficient Finetuning of Quantized LLMs", "source": "Arxiv", "date": "2023-05-23"},

    # lilian weng canonical posts
    {"url": "https://lilianweng.github.io/posts/2023-01-27-the-transformer-family-v2/", "title": "The Transformer Family Version 2.0", "source": "Lilian Weng", "date": "2023-01-27"},
    {"url": "https://lilianweng.github.io/posts/2021-01-02-attention-free-transformer/", "title": "Reduce Memory Costs of Transformers", "source": "Lilian Weng", "date": "2021-01-02"},
    {"url": "https://lilianweng.github.io/posts/2023-06-23-agent/", "title": "LLM Powered Autonomous Agents", "source": "Lilian Weng", "date": "2023-06-23"},

    # karpathy
    {"url": "https://karpathy.github.io/2022/03/14/lecun1989/", "title": "Deep Neural Nets: 33 years ago and 33 years from now", "source": "Karpathy", "date": "2022-03-14"},
]

HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

AI_KEYWORDS = ["ai", "llm", "model", "transformer", "neural", "gpt", "claude",
               "gemini", "diffusion", "reinforcement", "inference", "benchmark",
               "agent", "fine-tun", "quantiz", "embedding", "multimodal"]
