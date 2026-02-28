"""
News fetcher module - Fetches real-time finance, crypto, geopolitical news and economic calendar
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import json
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
            "CoinDesk":.coindesk.com/feed/",
            "https://www "CoinTelegraph": "https://cointelegraph.com/rss",
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

        # ========== 经济日历 ==========
        self.economic_calendar_feeds = {
            "Investing.com 经济日历": "https://www.investing.com/rss/calendar.rss",
            "ForexFactory 经济日历": "https://www.forexfactory.com/news.rss",
        }

        # 预设未来重要经济事件 (备用)
        self._upcoming_events = self._generate_upcoming_events()

    def _generate_upcoming_events(self) -> List[Dict[str, str]]:
        """生成未来一周重要经济事件"""
        events = []
        today = datetime.now()
        
        # 每周固定重要事件
        week_events = [
            # 周一
            {"day": 0, "time": "09:30 中国", "name": "中国GDP年率", "importance": "高", "type": "中国宏观"},
            {"day": 0, "time": "17:00 欧元区", "name": "欧元区制造业PMI", "importance": "中", "type": "欧洲宏观"},
            
            # 周二
            {"day": 1, "time": "08:30 澳大利亚", "name": "澳大利亚联储利率决议", "importance": "高", "type": "澳洲央行"},
            {"day": 1, "time": "17:00 德国", "name": "德国CPI年率", "importance": "中", "type": "欧洲宏观"},
            
            # 周三
            {"day": 2, "time": "20:30 美国", "name": "美国CPI月/年率", "importance": "极高", "type": "美国宏观"},
            {"day": 2, "time": "22:30 美国", "name": "美国EIA原油库存", "importance": "中", "type": "美国能源"},
            
            # 周四
            {"day": 3, "time": "02:00 美国", "name": "美联储利率决议", "importance": "极高", "type": "美国央行"},
            {"day": 3, "time": "02:30 美国", "name": "美联储主席鲍威尔讲话", "importance": "极高", "type": "美国央行"},
            {"day": 3, "time": "20:30 英国", "name": "英国央行利率决议", "importance": "高", "type": "英国央行"},
            {"day": 3, "time": "20:30 美国", "name": "美国PPI月率", "importance": "中", "type": "美国宏观"},
            
            # 周五
            {"day": 4, "time": "15:00 德国", "name": "德国GDP年率", "importance": "中", "type": "欧洲宏观"},
            {"day": 4, "time": "20:30 美国", "name": "美国零售销售月率", "importance": "高", "type": "美国宏观"},
            {"day": 4, "time": "21:15 美国", "name": "美国工业产出月率", "importance": "中", "type": "美国宏观"},
            {"day": 4, "time": "22:00 美国", "name": "美国密歇根大学消费者信心指数", "importance": "中", "type": "美国宏观"},
            
            # 周六
            {"day": 5, "time": "09:30 中国", "name": "中国1年期/5年期LPR", "importance": "高", "type": "中国央行"},
            
            # 周日
            {"day": 6, "time": "无重要事件", "name": "-", "importance": "-", "type": "-"},
        ]
        
        # 计算本周事件
        current_day = today.weekday()
        
        for event in week_events:
            days_until = event["day"] - current_day
            if days_until < 0:
                days_until += 7
            
            event_date = today + timedelta(days=days_until)
            
            if event["name"] != "-":
                events.append({
                    "title": f"【{event['importance']}】{event['name']}",
                    "description": f"发布时间: {event['time']} | 类型: {event['type']} | 重要性: {event['importance']}",
                    "date": event_date.strftime("%Y-%m-%d"),
                    "time": event["time"],
                    "importance": event["importance"],
                    "type": event["type"],
                    "source": "经济日历预判"
                })
        
        return events

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

    def fetch_economic_calendar(self, days_ahead: int = 7) -> List[Dict[str, str]]:
        """获取未来指定天数的经济日历事件"""
        logger.info(f"Fetching economic calendar for next {days_ahead} days...")
        
        calendar_events = []
        
        # 尝试从 RSS 获取经济日历
        for source_name, feed_url in self.economic_calendar_feeds.items():
            items = self.fetch_rss_feed(feed_url, 20)
            for item in items:
                item['source'] = source_name
                # 过滤出未来一周的事件
                if item.get('published'):
                    try:
                        pub_date = item['published']
                        # 尝试解析日期
                        for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%d']:
                            try:
                                parsed = datetime.strptime(pub_date[:25] if len(pub_date) > 25 else pub_date, fmt.replace(' %z', ''))
                                if parsed.date() <= (datetime.now() + timedelta(days=days_ahead)).date():
                                    calendar_events.append(item)
                                break
                            except:
                                continue
                    except:
                        calendar_events.append(item)
        
        # 如果没有获取到足够的事件，使用预设事件
        if len(calendar_events) < 3:
            logger.info("Using preset economic events")
            for event in self._upcoming_events:
                calendar_events.append({
                    "title": event["title"],
                    "description": event["description"],
                    "date": event["date"],
                    "time": event["time"],
                    "importance": event["importance"],
                    "type": event["type"],
                    "source": event["source"]
                })
        
        logger.info(f"Fetched {len(calendar_events)} economic calendar events")
        return calendar_events

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
            'economic_calendar': [],
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

        # Fetch Economic Calendar
        all_news['economic_calendar'] = self.fetch_economic_calendar(7)

        logger.info(f"Fetched: 中国股市 {len(all_news['china_stock'])}, 美国股市 {len(all_news['us_stock'])}, 虚拟货币 {len(all_news['crypto'])}, 宏观经济 {len(all_news['macro'])}, 中国政治 {len(all_news['china_politics'])}, 国际政治 {len(all_news['global_politics'])}, 经济日历 {len(all_news['economic_calendar'])}")

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
            'economic_calendar': '一周重要经济日历',
        }

        for key, name in categories.items():
            if news_data.get(key):
                formatted += f"## {name}\n\n"
                for i, item in enumerate(news_data[key], 1):
                    formatted += f"### {i}. {item['title']}\n"
                    formatted += f"**来源:** {item['source']}\n"
                    if item.get('description'):
                        desc = item['description'][:500] if len(item['description']) > 500 else item['description']
                        formatted += f"**摘要:** {desc}\n"
                    if item.get('date'):
                        formatted += f"**日期:** {item['date']}\n"
                    if item.get('time'):
                        formatted += f"**时间:** {item['time']}\n"
                    if item.get('importance'):
                        formatted += f"**重要性:** {item['importance']}\n"
                    if item.get('link'):
                        formatted += f"**链接:** {item['link']}\n"
                    formatted += "\n"

        return formatted
