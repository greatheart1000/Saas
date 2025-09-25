#!/usr/bin/env python3
"""
crawler_playwright.py

完整可运行的 Playwright 异步爬虫：
- 并发控制：CONCURRENCY（默认 20）
- RPS 限制：SimpleRateLimiter（可配置）
- 浏览器：Playwright (chromium)
- 代理池：PROXY_LIST （每个 task 可指定 proxy dict 或 None）
- 反爬：随机 UA、随机延迟、重试
- 登录模拟模板：login_if_needed
- MySQL：使用 aiomysql 创建数据库与表并写入抓取结果

请在合规和许可前提下运行爬虫并尊重目标站点 robots.txt。
"""

import asyncio
import logging
import random
import time
from typing import List, Optional

import aiomysql
from fake_useragent import UserAgent
from playwright.async_api import async_playwright, Browser, Page

# ---------- Configuration ----------
START_URL = "http://www.liuxuehr.com/gaoxiao/index.html"
CONCURRENCY = 20  # 并发页面数
MAX_REQUESTS_PER_SECOND = 50  # RPS 上限；设为较大值以不严格限制
MAX_RETRIES = 3
NAV_TIMEOUT = 30 * 1000  # ms

# Proxy list: each entry is either None (no proxy) or dict accepted by Playwright, e.g.:
# {"server": "http://host:port"} or {"server": "http://user:pass@host:port"}.
# If you need username/password separately you can provide {"server": "http://host:port", "username":"...", "password":"..."}
PROXY_LIST: List[Optional[dict]] = [
    None,
    # Example:
    # {"server": "http://127.0.0.1:8000"},
    # {"server": "http://user:pass@1.2.3.4:3128"},
]

# MySQL credentials (you provided these)
MYSQL_HOST = "127.0.0.1"
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"
MYSQL_DB = "liuxuehr_scrape"
MYSQL_TABLE = "gaoxiao_jobs"

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("crawler")

# ---------- Rate limiter (simple token-bucket) ----------
class SimpleRateLimiter:
    """
    Simple token-bucket rate limiter for asyncio.
    max_calls: tokens per period
    period: seconds
    """
    def __init__(self, max_calls: int, period: float):
        self.max_calls = float(max_calls)
        self.period = float(period)
        self.allowance = float(max_calls)
        self.last_check = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            while True:
                current = time.monotonic()
                time_passed = current - self.last_check
                self.last_check = current
                self.allowance += time_passed * (self.max_calls / self.period)
                if self.allowance > self.max_calls:
                    self.allowance = self.max_calls
                if self.allowance >= 1.0:
                    self.allowance -= 1.0
                    return
                # compute sleep time (simple)
                await asyncio.sleep((1.0 - self.allowance) * (self.period / self.max_calls))

RATE_LIMITER = SimpleRateLimiter(max_calls=MAX_REQUESTS_PER_SECOND, period=1.0)

# ---------- User agent ----------
ua_generator = UserAgent()

def get_random_ua() -> str:
    try:
        return ua_generator.random
    except Exception:
        return ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")

def get_next_proxy(index: int) -> Optional[dict]:
    if not PROXY_LIST:
        return None
    return PROXY_LIST[index % len(PROXY_LIST)]

# ---------- MySQL helpers ----------
async def init_mysql_pool():
    # create database if not exists, then return pool connected to that db
    logger.info("Ensuring MySQL database exists...")
    try:
        conn = await aiomysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, autocommit=True)
        async with conn.cursor() as cur:
            await cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()
    except Exception as e:
        logger.error("Failed to connect/create database: %s", e)
        raise

    pool = await aiomysql.create_pool(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD,
                                      db=MYSQL_DB, autocommit=True, minsize=1, maxsize=10)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(f"""
                CREATE TABLE IF NOT EXISTS `{MYSQL_TABLE}` (
                    `id` INT PRIMARY KEY AUTO_INCREMENT,
                    `url` VARCHAR(1000) NOT NULL,
                    `title` VARCHAR(1000),
                    `content` MEDIUMTEXT,
                    `fetched_at` DATETIME DEFAULT CURRENT_TIMESTAMP
                ) CHARSET=utf8mb4;
            """)
    logger.info("MySQL pool ready and table ensured.")
    return pool

async def save_item(pool, item: dict):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"INSERT INTO `{MYSQL_TABLE}` (url, title, content) VALUES (%s, %s, %s);",
                (item.get("url"), item.get("title"), item.get("content"))
            )

# ---------- Crawling logic ----------
async def login_if_needed(page: Page):
    """
    登录模拟模板。如果需要登录请修改这里的逻辑与选择器。
    当前目标不需要登录，函数保持空。
    """
    return

async def fetch_page(browser: Browser, url: str, pool, semaphore: asyncio.Semaphore, proxy: Optional[dict], task_index: int):
    """
    Fetch a page with optional proxy and save to MySQL.
    Each task creates a new browser context (so UA/proxy are per-task).
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        attempt += 1
        context = None
        page = None
        try:
            await RATE_LIMITER.acquire()
            async with semaphore:
                ua = get_random_ua()
                context_kwargs = {
                    "user_agent": ua,
                    "locale": "zh-CN",
                }
                if proxy:
                    context_kwargs["proxy"] = proxy

                logger.info(f"[task {task_index}] (attempt {attempt}) creating context, proxy={proxy is not None}")
                context = await browser.new_context(**context_kwargs)
                page = await context.new_page()
                page.set_default_navigation_timeout(NAV_TIMEOUT)

                # slight random delay to mimic human
                await asyncio.sleep(0.2 + random.random() * 0.8)

                # login if needed (template)
                # await login_if_needed(page)

                logger.info(f"[task {task_index}] navigating to {url} using UA-start:{ua[:60]}...")
                await page.goto(url, wait_until="networkidle")

                # wait a bit for content to finish and to reduce bot fingerprinting
                await asyncio.sleep(0.5 + random.random() * 1.5)

                title = await page.title()
                # get text content; if you want HTML use inner_html()
                try:
                    content = await page.locator("body").inner_text()
                except Exception:
                    # fallback to content of <html>
                    try:
                        content = await page.content()
                    except Exception:
                        content = ""

                item = {"url": url, "title": title or "", "content": content or ""}
                await save_item(pool, item)
                logger.info(f"[task {task_index}] saved item (title len {len(item['title'])}, content len {len(item['content'])})")

                # cleanup
                try:
                    await page.close()
                except Exception:
                    pass
                try:
                    await context.close()
                except Exception:
                    pass

                return True

        except Exception as e:
            logger.warning(f"[task {task_index}] error attempt {attempt} for {url}: {e}")
            # cleanup
            try:
                if page:
                    await page.close()
            except Exception:
                pass
            try:
                if context:
                    await context.close()
            except Exception:
                pass
            # backoff
            await asyncio.sleep(1.0 + random.random() * 2.0 * attempt)
    logger.error(f"[task {task_index}] failed to fetch {url} after {MAX_RETRIES} attempts")
    return False

async def main():
    # global handlers for debugging
    def handle_exc(loop, context):
        logger.error("Global exception: %s", context)
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exc)

    pool = await init_mysql_pool()

    playwright = await async_playwright().start()
    # Optionally set executable_path if your environment needs a system chromium/chrome:
    # browser = await playwright.chromium.launch(executable_path="/usr/bin/chromium-browser", headless=True, args=["--no-sandbox"])
    browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])

    semaphore = asyncio.Semaphore(CONCURRENCY)

    tasks = []
    # For the simple case we only fetch the start page.
    # If you want to crawl detail links, first fetch index page and extract links, then schedule more fetch_page tasks.
    proxy_for_task = get_next_proxy(0)
    tasks.append(fetch_page(browser, START_URL, pool, semaphore, proxy_for_task, task_index=0))

    # Wait for tasks
    results = await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("All tasks done. Results: %s", results)

    # cleanup
    await browser.close()
    await playwright.stop()
    pool.close()
    await pool.wait_closed()
    logger.info("Crawler finished.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
