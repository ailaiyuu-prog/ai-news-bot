"""
AI News Generator using configurable LLM providers
"""
from typing import List, Optional, Dict
import json
import re
from ..logger import setup_logger
from ..config import LANGUAGE_NAMES
from .web_search import WebSearchTool, get_search_tool_definition
from .fetcher import NewsFetcher
from ..llm_providers import get_llm_provider


logger = setup_logger(__name__)


class NewsGenerator:
    """Generate AI news digest using configurable LLM providers"""

    def __init__(
        self,
        provider_name: str = "deepseek",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_web_search: bool = False
    ):
        """Initialize the NewsGenerator."""
        self.provider = get_llm_provider(
            provider_name=provider_name,
            api_key=api_key,
            model=model
        )

        self.enable_web_search = enable_web_search
        self.search_tool = WebSearchTool() if enable_web_search else None
        self.news_fetcher = NewsFetcher()
        logger.info(
            f"NewsGenerator initialized with {self.provider.provider_name} "
            f"(model: {self.provider.model}, web_search: {enable_web_search})"
        )

    def _format_news_with_ids(self, news_data: Dict) -> tuple:
        """Format news with unique IDs for selection stage."""
        formatted = "# 财经与政治新闻精选\n\n"
        news_items = {}
        item_id = 1

        categories = {
            'china_stock': '中国股市',
            'us_stock': '美国股市',
            'crypto': '虚拟货币',
            'macro': '宏观经济',
            'china_politics': '中国政治',
            'global_politics': '国际政治',
        }

        for cat_key, cat_name in categories.items():
            if news_data.get(cat_key):
                formatted += f"## {cat_name}\n\n"
                for item in news_data[cat_key]:
                    news_id = f"{cat_key}-{item_id}"
                    news_items[news_id] = item

                    formatted += f"### [{news_id}] {item['title']}\n"
                    formatted += f"**来源:** {item['source']}\n"
                    if item['description']:
                        formatted += f"**摘要:** {item['description'][:400]}...\n"
                    if item['published']:
                        formatted += f"**发布时间:** {item['published']}\n"
                    formatted += "\n"
                    item_id += 1

        return formatted, news_items

    def generate_news_digest_from_sources(
        self,
        max_tokens: int = 8000,
        language: str = "zh",
        max_items_per_source: int = 5,
        stage1_template: Optional[str] = None,
        stage2_template: Optional[str] = None
    ) -> str:
        """Fetch real-time news and generate a digest using two-stage prompt chaining."""
        try:
            # Fetch real-time news
            logger.info("Fetching real-time finance and geopolitics news from sources...")
            news_data = self.news_fetcher.fetch_recent_news(
                language=language,
                max_items_per_source=max_items_per_source
            )

            # Check if we have any news
            total_fetched = sum(len(v) for v in news_data.values())
            if total_fetched == 0:
                error_msg = "No news items fetched from RSS sources. Please check your network connection or RSS feed availability."
                logger.error(error_msg)
                raise Exception(error_msg)

            # Format news with unique IDs for selection
            formatted_news, news_items = self._format_news_with_ids(news_data)
            total_items = len(news_items)

            logger.info(f"Starting two-stage prompt chaining with {total_items} news items")

            # ============================================================
            # STAGE 1: Selection
            # ============================================================
            logger.info(f"Stage 1: Analyzing and selecting high-quality news items...")

            if stage1_template is None:
                from ..config import Config
                config = Config()
                stage1_template = config.stage1_prompt_template

            selection_prompt = stage1_template.format(
                formatted_news=formatted_news,
                total_items=total_items
            )

            messages = [{"role": "user", "content": selection_prompt}]
            selection_response = self.provider.generate(
                messages=messages,
                max_tokens=4000
            )

            # Parse selected IDs
            json_match = re.search(r'\[[\s\S]*?\]', selection_response)
            if not json_match:
                logger.warning("Could not parse JSON from selection response, using fallback")
                selected_ids = list(news_items.keys())[:18]
            else:
                try:
                    selected_ids = json.loads(json_match.group(0))
                    selected_ids = [id for id in selected_ids if id in news_items]

                    if len(selected_ids) < 15:
                        logger.warning(f"Only {len(selected_ids)} items selected, adding more")
                        remaining = [id for id in news_items.keys() if id not in selected_ids]
                        selected_ids.extend(remaining[:18 - len(selected_ids)])
                    elif len(selected_ids) > 20:
                        logger.warning(f"{len(selected_ids)} items selected, trimming to 20")
                        selected_ids = selected_ids[:20]

                except json.JSONDecodeError:
                    logger.warning("JSON parse error, using fallback selection")
                    selected_ids = list(news_items.keys())[:18]

            logger.info(f"Stage 1 completed: Selected {len(selected_ids)} news items")

            # ============================================================
            # STAGE 2: Summarization
            # ============================================================
            logger.info(f"Stage 2: Creating detailed summaries for selected items...")

            # Format selected news for summarization
            formatted_selected = "# 精选财经与政治新闻\n\n"
            for news_id in selected_ids:
                item = news_items[news_id]
                formatted_selected += f"### [{news_id}] {item['title']}\n"
                formatted_selected += f"**来源:** {item['source']}\n"
                if item['description']:
                    formatted_selected += f"**内容:** {item['description']}\n"
                formatted_selected += f"**链接:** {item['link']}\n"
                if item['published']:
                    formatted_selected += f"**发布时间:** {item['published']}\n"
                formatted_selected += "\n"

            if stage2_template is None:
                from ..config import Config
                config = Config()
                stage2_template = config.stage2_prompt_template

            summarization_prompt = stage2_template.format(
                count=len(selected_ids),
                selected_news=formatted_selected
            )

            # Add language instruction
            if language and language.lower() != "en":
                language_name = LANGUAGE_NAMES.get(language.lower(), language.upper())
                summarization_prompt += f"\n\n重要提示：请完全使用{language_name}回复。"

            # Execute Stage 2
            messages = [{"role": "user", "content": summarization_prompt}]
            response_text = self.provider.generate(
                messages=messages,
                max_tokens=max_tokens
            )

            # Add footer
            footer = "\n\n---\n\n*由 [财经新闻机器人](https://github.com/giftedunicorn/ai-news-bot) 自动生成*"
            response_text += footer

            logger.info("Stage 2 completed: News digest generated successfully")
            logger.info(f"Two-stage prompt chaining completed: {total_items} items → {len(selected_ids)} selected → full digest")

            return response_text

        except Exception as e:
            logger.error(f"Failed to generate news digest from sources: {str(e)}", exc_info=True)
            raise
