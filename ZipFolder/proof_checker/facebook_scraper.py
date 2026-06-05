import asyncio
import random
import re
from datetime import datetime

from playwright.async_api import async_playwright


# ============================================================
# FILTERS
# ============================================================

def is_noise(text):
    if not text:
        return True

    text = text.strip().lower()

    bad = [
        "like",
        "reply",
        "replies",
        "share",
        "follow",
        "comment",
        "comments",
        "most relevant",
        "write a comment",
        "send message",
        "edited",
        "author",
        "meta",
        "facebook",
    ]

    if text in bad:
        return True

    # timestamps like 1h, 2d, 3w
    if re.fullmatch(r"\d+[smhdwy]", text):
        return True

    if text.isdigit():
        return True

    return False


# ============================================================
# CAPTCHA / SECURITY CHECK
# ============================================================

async def detect_captcha(page):
    html = await page.content()

    suspicious = [
        "captcha",
        "security check",
        "verify you are human",
        "unusual activity",
    ]

    for item in suspicious:
        if item.lower() in html.lower():
            return True

    return False


# ============================================================
# COMMENTS PANEL
# ============================================================

async def find_comments_panel(page):
    print("🔍 Locating Facebook comments panel...")

    panel = await page.evaluate_handle("""
        () => {
            const all = Array.from(document.querySelectorAll("*"));

            return all.find(el => {
                const style = window.getComputedStyle(el);

                const scrollable =
                    style.overflowY === "scroll" ||
                    style.overflowY === "auto";

                return (
                    scrollable &&
                    el.scrollHeight > el.clientHeight + 300
                );
            }) || document.body;
        }
    """)

    print("✅ Facebook comments panel found\n")

    return panel


async def scroll_comments_panel(panel):
    amount = random.randint(1000, 2200)

    await panel.evaluate(f"(el) => el.scrollBy(0, {amount})")

    await asyncio.sleep(random.uniform(1.8, 3.2))


# ============================================================
# SCRAPE COMMENTS
# ============================================================

async def scrape_facebook_comments_from_page(page, max_comments=30):
    comments = []
    seen = set()
    same_rounds = 0

    panel = await find_comments_panel(page)

    while len(comments) < max_comments and same_rounds < 10:
        await scroll_comments_panel(panel)

        blocks = await page.query_selector_all('div[aria-label="Comment"]')

        if not blocks:
            blocks = await page.query_selector_all('div[role="article"]')

        print(f"🔍 Found {len(blocks)} possible Facebook comments")

        new_found = 0

        for block in blocks:
            try:
                text = await block.inner_text()

                if not text:
                    continue

                lines = [
                    line.strip()
                    for line in text.split("\n")
                    if line.strip()
                ]

                cleaned_lines = []

                for line in lines:
                    if is_noise(line):
                        continue

                    cleaned_lines.append(line)

                lines = cleaned_lines

                if len(lines) < 2:
                    continue

                username = lines[0]

                comment_parts = []

                for line in lines[1:]:
                    if is_noise(line):
                        continue

                    if re.fullmatch(r"\d+[smhdwy]", line):
                        break

                    comment_parts.append(line)

                comment = " ".join(comment_parts).strip()

                if not comment:
                    continue

                if len(comment) < 2:
                    continue

                uid = f"{username}:{comment[:100]}"

                if uid in seen:
                    continue

                seen.add(uid)

                comments.append({
                    "index": len(comments) + 1,
                    "username": username,
                    "comment": comment,
                    "scraped_at": datetime.now().isoformat()
                })

                new_found += 1

                print(f"\n✅ @{username}")
                print(f"💬 {comment[:120]}")

                if len(comments) >= max_comments:
                    break

            except Exception as e:
                print("⚠ Facebook extraction error:", e)
                continue

        if new_found == 0:
            same_rounds += 1
            print(f"\n⚠ No new Facebook comments found ({same_rounds}/10)\n")
        else:
            same_rounds = 0

        print(f"\n📦 Total Facebook comments collected: {len(comments)}\n")

    return comments


# ============================================================
# MAIN FACEBOOK SCRAPER
# ============================================================

async def scrape_facebook_comments(post_url, max_comments=30, headless=False):
    """
    Facebook public post scraper.
    No login required for public comments.
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=80,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        )

        context = await browser.new_context(
            viewport={
                "width": 1280,
                "height": 900
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )

        page = await context.new_page()

        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            window.chrome = {
                runtime: {}
            };

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1,2,3]
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        print("\n📱 Opening Facebook post...\n")

        await page.goto(
            post_url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        await page.wait_for_timeout(7000)

        print("Current Facebook URL:", page.url)

        captcha = await detect_captcha(page)

        if captcha:
            print("\n⚠ Facebook human verification detected.")
            print("Complete it manually in opened browser.")
            print("Then come back to terminal.\n")

            input("Press Enter after verification: ")

            await page.wait_for_timeout(4000)

        comments = await scrape_facebook_comments_from_page(
            page,
            max_comments=max_comments
        )

        print("\n" + "=" * 60)
        print(f"✅ Facebook scraping done. Total comments: {len(comments)}")
        print("=" * 60)

        await browser.close()

        return comments


def run_facebook_scraper_sync(post_url, max_comments=30):
    return asyncio.run(
        scrape_facebook_comments(
            post_url=post_url,
            max_comments=max_comments,
            headless=False
        )
    )