"""
News fetcher module - Fetches real-time finance, crypto and geopolitical news
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from ..logger import setup_logger


logger = setup_logger(__name__)


class NewsFetcher:
    """Fetch real-time finance, crypto and geopolitical news from RSS feeds"""

    def __init__(self):
        """Initialize the news fetcher"""
        
        # ========== 中国股市 ==========
        self.china_stock_feeds = {
            "新浪财经": "https://finance.sina.com.cn/stock/",
            "东方财富": "https://www.eastmoney.com/",
            "腾讯财经": "https://finance.qq.com/stock/",
            "同花顺": "https://www.10jqka.com.cn/",
            "雪球": "https://xueqiu.com/hq",
            "证券时报": "http://www.stcn.com/",
            "第一财经": "https://www.yicai.com/news/",
            "财新网": "http://www.caixin.com/",
        }

        # ========== 美国股市 ==========
        self.us_stock_feeds = {
            "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
            "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
            "Reuters Business": "https://www.reutersagency.com/feed/?best-topics=business-finance",
            "WSJ": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
            "Bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
            "Barron's": "https://feeds.barrons.com/rss/all",
        }

        # ========== 虚拟货币 ==========
        self.crypto_feeds = {
            "CoinDesk": "https://www.coindesk.com/feed/",
            "CoinTelegraph": "https://cointelegraph.com/rss",
            "Decrypt": "https://decrypt.co/feed",
            "The Block": "https://www.theblock.co/feed",
            "CryptoSlate": "https://cryptoslate.com/feed/",
            "Binance Blog": "https://www.binance.com/en/blog/feed",
            "吴说区块链": "https://www.wu-talk.com/feed",
        }

        # ========== 宏观经济 ==========
        self.macro_feeds = {
            "Investing.com": "https://www.investing.com/rss/news.rss",
            "TradingEconomics": "https://tradingeconomics.com/rss",
            "美联储": "https://www.federalreserve.gov/feeds/press_all.xml",
            "IMF": "https://www.imf.org/external/rss/rss.aspx?type=news",
            "世界银行": "https://feeds.worldbank.org/RSS/RSS2.xml",
            "华尔街见闻": "https://wallstreetcn.com/rss",
            "彭博社中文": "https://www.bloomberg.com/feeds/markets",
        }

        # ========== 中国政治 ==========
        self.china_politics_feeds = {
            "新华社": "http://www.xinhuanet.com/politics/news_politics.xml",
            "人民网": "http://politics.people.com.cn/rss/zzb.xml",
            "环球时报": "https://global.huanqiu.com/rss",
            "中国日报": "https://cn.chinadaily.com.cn/rss",
            "参考消息": "https://www.cankaoxiaoxi.com/feed",
            "外交部": "https://www.mfa.gov.cn/web/fyrbt_673021/jzzwl_673057/rss.xml",
        }

        # ========== 国际政治 ==========
        self.global_politics_feeds = {
            "BBC News": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "Reuters": "https://www.reutersagency.com/feed/?best-topics=politics",
            "AP News": "https://feeds.apnews.com/apnews/topnews",
            "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
            "欧盟": "https://ec.europa.eu/rss/en/rss.xml",
            "联合国": "https://news.un.org/rss/en/sitemap.xml",
        }

    def fetch_rss_feed(self, feed_url: str, max_items: int = 10) -> List[Dict[str, str]]:
        """Fetch news items from an RSS feed."""
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(feed_url, headers=headers, timeout=10)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            items = []

            if root.tag == 'rss':
                news_items = root.findall('.//item')[:max_items]
                for item in news_items:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')

                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.text if link is not None else '',
                        'description': self._clean_html(description.text if description is not None else ''),
                        'published': pub_date.text if pub_date is not None else '',
                    })
            else:
                namespace = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('.//atom:entry', namespace)[:max_items]
                for entry in entries:
                    title = entry.find('atom:title', namespace)
                    link = entry.find('atom:link', namespace)
                    summary = entry.find('atom:summary', namespace)
                    updated = entry.find('atom:updated', namespace)

                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.get('href', '') if link is not None else '',
                        'description': self._clean_html(summary.text if summary is not None else ''),
                        'published': updated.text if updated is not None else '',
                    })

            logger.info(f"Fetched {len(items)} items from RSS feed")
            return items

        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {feed_url}: {str(e)}")
            return []

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()

    def fetch_recent_news(
        self,
        language: str = "zh",
        max_items_per_source: int = 5
    ) -> Dict[str, List[Dict[str, str]]]:
        """Fetch recent finance, crypto and geopolitical news."""
        logger.info("Fetching recent finance and geopolitics news from all sources...")

        all_news = {
            'china_stock': [],
            'us_stock': [],
            'crypto': [],
            'macro': [],
            'china_politics': [],
            'global_politics': [],
        }

        # Fetch China Stock news
        for source_name, feed_url in self.china_stock_feeds.items():
            items = self.fetch_rss_feed(feed_url, max_items_per_source)
            for item in items:
                item['source'] = source_name
                all_news['china_stock'].append(item)

        # Fetch US Stock news
        for source_name, feed_url in self.us_stock_feeds.items():
            items = self.fetch_rss_feed(feed_url, max_items_per_source)
            for item in items:
                item['source'] = source_name
                all_news['us_stock'].append(item)

        # Fetch Crypto news
        for source_name, feed_url in self.crypto_feeds.items():
            items = self.fetch_rss_feed(feed_url, max_items_per_source)
            for item in items:
                item['source'] = source_name
                all_news['crypto'].append(item)

        # Fetch Macro news
        for source_name, feed_url in self.macro_feeds.items():
            items = self.fetch_rss_feed(feed_url, max_items_per_source)
            for item in items:
                item['source'] = source_name
                all_news['macro'].append(item)

        # Fetch China Politics news
        for source_name, feed_url in self.china_politics_feeds.items():
            items = self.fetch_rss_feed(feed_url, max_items_per_source)
            for item in items:
                item['source'] = source_name
                all_news['china_politics'].append(item)

        # Fetch Global Politics news
        for source_name, feed_url in self.global_politics_feeds.items():
            items = self.fetch_rss_feed(feed_url, max_items_per_source)
            for item in items:
                item['source'] = source_name
                all_news['global_politics'].append(item)

        logger.info(f"Fetched: 中国股市 {len(all_news['china_stock'])}, 美国股市 {len(all_news['us_stock'])}, 虚拟货币 {len(all_news['crypto'])}, 宏观经济 {len(all_news['macro'])}, 中国政治 {len(all_news['china_politics'])}, 国际政治 {len(all_news['global_politics'])}")

        return all_news

    def format_news_for_summary(self, news_data: Dict[str, List[Dict[str, str]]]) -> str:
        """Format fetched news into a text suitable for AI summarization."""
        formatted = "# 财经与政治新闻汇总\n\n"

        categories = {
            'china_stock': '中国股市',
            'us_stock': '美国股市',
            'crypto': '虚拟货币',
            'macro': '宏观经济',
            'china_politics': '中国政治',
            'global_politics': '国际政治',
        }

        for key, name in categories.items():
            if news_data.get(key):
                formatted += f"## {name}\n\n"
                for i, item in enumerate(news_data[key], 1):
                    formatted += f"### {i}. {item['title']}\n"
                    formatted += f"**来源:** {item['source']}\n"
                    if item['description']:
                        desc = item['description'][:500] if len(item['description']) > 500 else item['description']
                        formatted += f"**摘要:** {desc}\n"
                    formatted += f"**链接:** {item['link']}\n"
                    if item['published']:
                        formatted += f"**发布时间:** {item['published']}\n"
                    formatted += "\n"

        return formatted
