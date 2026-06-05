import asyncio
import re
from datetime import datetime

from playwright.async_api import async_playwright


def is_noise(text: str) -> bool:
    if not text:
        return True

    text = text.lower().strip()

    bad = [
        "reply",
        "replies",
        "view replies",
        "hide replies",
        "read more",
        "show less",
        "subscribe",
        "share",
    ]

    if text in bad:
        return True

    if re.fullmatch(r"\d+[smhd]", text):
        return True

    return len(text) <= 1


async def force_scroll_comments(page):
    await page.mouse.move(640, 400)
    await page.mouse.wheel(0, 1500)
    await asyncio.sleep(2.5)


async def load_youtube_comments_section(page):
    print("⏳ Scrolling to load YouTube comments section...")

    for attempt in range(30):
        await page.mouse.move(640, 400)
        await page.mouse.wheel(0, 700)
        await page.wait_for_timeout(1500)

        found = await page.query_selector("ytd-comment-thread-renderer")

        if found:
            print(f"✅ YouTube comments section loaded. Attempt {attempt + 1}")
            return True

    print("❌ YouTube comments did not load after 30 scroll attempts.")
    return False


async def scrape_youtube_comments_from_page(page, max_comments=30):
    comments = []
    seen = set()
    same_rounds = 0

    while len(comments) < max_comments and same_rounds < 20:
        await force_scroll_comments(page)
        await page.wait_for_timeout(2000)

        threads = await page.query_selector_all("ytd-comment-thread-renderer")

        print(f"🔍 Found {len(threads)} YouTube comment threads")

        new_found = 0

        for thread in threads:
            try:
                author_el = await thread.query_selector("#author-text span")
                text_el = await thread.query_selector("#content-text")
                time_el = await thread.query_selector(".published-time-text a")
                likes_el = await thread.query_selector("#vote-count-middle")

                author = (await author_el.inner_text()).strip() if author_el else "Unknown"
                comment = (await text_el.inner_text()).strip() if text_el else ""
                published = (await time_el.inner_text()).strip() if time_el else ""
                likes = (await likes_el.inner_text()).strip() if likes_el else "0"

                if is_noise(comment):
                    continue

                uid = f"{author}:{comment[:80]}"

                if uid in seen:
                    continue

                seen.add(uid)

                comments.append({
                    "index": len(comments) + 1,
                    "username": author,
                    "comment": comment,
                    "likes": likes,
                    "published": published,
                    "scraped_at": datetime.now().isoformat()
                })

                new_found += 1

                print(f"✅ @{author} -> {comment[:80]}")

                if len(comments) >= max_comments:
                    break

            except Exception as e:
                print("⚠ YouTube extraction error:", e)
                continue

        if new_found == 0:
            same_rounds += 1
            print(f"⚠ No new YouTube comments found ({same_rounds}/20)")
        else:
            same_rounds = 0

        print(f"\n📦 YouTube progress: {len(comments)} / {max_comments}\n")

    return comments


async def scrape_youtube_comments(video_url, max_comments=30, headless=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=50,
            args=[
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = await browser.new_context(
            viewport={
                "width": 1280,
                "height": 800
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "Chrome/124 Safari/537.36"
            )
        )

        page = await context.new_page()

        print("\n📺 Opening YouTube video...")
        print("YouTube URL:", video_url)

        await page.goto(
            video_url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        await page.wait_for_timeout(5000)

        loaded = await load_youtube_comments_section(page)

        if not loaded:
            await browser.close()
            raise Exception("YouTube comments section did not load.")

        comments = await scrape_youtube_comments_from_page(
            page,
            max_comments=max_comments
        )

        print("\n" + "=" * 60)
        print(f"✅ YouTube scraping done. Total comments: {len(comments)}")
        print("=" * 60)

        await browser.close()

        return comments


def run_youtube_scraper_sync(video_url, max_comments=30):
    return asyncio.run(
        scrape_youtube_comments(
            video_url=video_url,
            max_comments=max_comments,
            headless=False
        )
    )