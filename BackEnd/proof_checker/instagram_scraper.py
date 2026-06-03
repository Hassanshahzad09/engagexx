import asyncio
import random
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright


INSTAGRAM_SESSION_FILE = "instagram_session.json"


# ============================================================
# URL FIXER
# ============================================================

def force_comments_url(url):
    """
    Converts Instagram post/reel URL into /comments/ endpoint.

    Example:
    https://www.instagram.com/p/DZIeMh8G1O-/?utm_source=abc

    Becomes:
    https://www.instagram.com/p/DZIeMh8G1O-/comments/
    """

    url = url.strip()

    # remove query params like ?utm_source=...
    url = url.split("?")[0]

    # remove ending slash
    url = url.rstrip("/")

    # if already comments endpoint
    if url.endswith("/comments"):
        return url + "/"

    return url + "/comments/"


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):
    if not text:
        return ""

    return " ".join(str(text).lower().strip().split())


def clean_username(username):
    if not username:
        return ""

    return str(username).lower().replace("@", "").strip()


def is_bad_text(text):
    bad_words = [
        "like",
        "likes",
        "reply",
        "view replies",
        "more",
        "see translation",
        "home",
        "reels",
        "messages",
        "edit",
        "follow",
        "following",
        "load more comments",
        "suggested for you",
    ]

    text = text.lower().strip()

    if text in bad_words:
        return True

    # timestamps like 2d, 3h, 4w
    if len(text) <= 4 and any(x in text for x in ["h", "m", "d", "w"]):
        return True

    return False


# ============================================================
# ONE-TIME SESSION LOGIN
# ============================================================

async def save_instagram_session():
    """
    Run one time only:
    python manage.py save_instagram_session

    It opens browser.
    You login manually.
    Then it saves instagram_session.json.
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False
        )

        context = await browser.new_context(
            viewport={"width": 432, "height": 932},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.0 Mobile/15E148 Safari/604.1"
            )
        )

        page = await context.new_page()

        await page.goto(
            "https://www.instagram.com/accounts/login/",
            wait_until="domcontentloaded",
            timeout=60000
        )

        print("\n" + "=" * 55)
        print("LOGIN TO INSTAGRAM")
        print("=" * 55)
        print("1. Login manually in the opened browser.")
        print("2. Wait until Instagram home/feed opens.")
        print("3. Come back to terminal.")
        print("4. Press Enter.")
        print("=" * 55)

        input("Press Enter AFTER Instagram login is complete: ")

        await page.wait_for_timeout(3000)

        await context.storage_state(path=INSTAGRAM_SESSION_FILE)

        print(f"✅ Instagram session saved successfully as {INSTAGRAM_SESSION_FILE}")

        await browser.close()


# ============================================================
# SCROLL
# ============================================================

async def human_scroll(panel):
    scroll_amount = random.randint(800, 1800)
    delay = random.randint(1500, 3500)

    await panel.evaluate(f"(el) => el.scrollBy(0, {scroll_amount})")
    await asyncio.sleep(delay / 1000)


# ============================================================
# NAVIGATE POST
# ============================================================

async def navigate_to_instagram_post(page, url, retries=3):
    url = force_comments_url(url)

    print("Final Instagram comments URL:", url)

    for attempt in range(1, retries + 1):
        try:
            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            await page.wait_for_timeout(5000)

            print("Current browser URL:", page.url)

            if "accounts/login" in page.url:
                print("❌ Instagram redirected to login page.")
                return False

            if "/p/" not in page.url and "/reel/" not in page.url:
                print("⚠ Unexpected Instagram redirect:", page.url)
                await page.wait_for_timeout(3000)
                continue

            print(f"✅ Instagram post loaded successfully. Attempt {attempt}")
            return True

        except Exception as e:
            print("⚠ Instagram navigation error:", e)
            await page.wait_for_timeout(3000)

    print("❌ Failed to open Instagram post.")
    return False


# ============================================================
# SCRAPE COMMENTS
# ============================================================

async def scrape_instagram_comments_from_page(page, max_comments=30):
    comments = []
    seen = set()

    selector_failures = {
        "username": 0,
        "comment": 0,
    }

    print("🔄 Locating Instagram comments panel...")

    comments_panel = await page.evaluate_handle("""
        () => {
            const all = Array.from(document.querySelectorAll("*"));

            return all.find(el => {
                const style = window.getComputedStyle(el);
                const overflowY = style.overflowY;

                const isScrollable =
                    (overflowY === "scroll" || overflowY === "auto") &&
                    el.scrollHeight > el.clientHeight + 50;

                return isScrollable;
            }) || document.body;
        }
    """)

    print("✅ Comments panel found\n")

    same_count_rounds = 0

    while len(comments) < max_comments and same_count_rounds < 10:
        await human_scroll(comments_panel)

        blocks = await page.query_selector_all("div")
        new_found = 0

        print(f"🔍 Scanning {len(blocks)} blocks...")

        for block in blocks:
            try:
                text = await block.inner_text()

                if not text:
                    continue

                lines = [line.strip() for line in text.split("\n") if line.strip()]

                if len(lines) < 2:
                    continue

                username = lines[0]
                comment = lines[1]

                if is_bad_text(username):
                    selector_failures["username"] += 1
                    continue

                if is_bad_text(comment):
                    selector_failures["comment"] += 1
                    continue

                if len(comment) < 2:
                    continue

                if "follow" in comment.lower():
                    continue

                uid = f"{username}:{comment[:80]}"

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

                print(f"✅ @{username}: {comment[:70]}")

                if len(comments) >= max_comments:
                    break

            except Exception as e:
                print("⚠ Instagram extraction error:", e)
                continue

        if new_found == 0:
            same_count_rounds += 1
            print(f"⚠ No new Instagram comments found ({same_count_rounds}/10)")
        else:
            same_count_rounds = 0

        print("\n📊 Selector Failure Stats:")
        print(selector_failures)
        print(f"📦 Total Instagram comments collected: {len(comments)}\n")

    return comments


# ============================================================
# MAIN SESSION-BASED SCRAPER
# ============================================================

async def scrape_instagram_comments(post_url, max_comments=30, headless=False):
    """
    Uses saved Instagram session.
    No manual login every time.
    """

    if not Path(INSTAGRAM_SESSION_FILE).exists():
        raise Exception(
            "Instagram session not found. First run: python manage.py save_instagram_session"
        )

    post_url = force_comments_url(post_url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless
        )

        context = await browser.new_context(
            storage_state=INSTAGRAM_SESSION_FILE,
            viewport={"width": 432, "height": 932},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.0 Mobile/15E148 Safari/604.1"
            )
        )

        page = await context.new_page()

        success = await navigate_to_instagram_post(page, post_url)

        if not success:
            await browser.close()
            raise Exception(
                "Instagram post did not open. Session may be expired. Run: python manage.py save_instagram_session"
            )

        await page.wait_for_timeout(3000)

        comments = await scrape_instagram_comments_from_page(
            page,
            max_comments=max_comments
        )

        print("\n" + "=" * 55)
        print(f"✅ Instagram scraping done. Total comments: {len(comments)}")
        print("=" * 55)

        await browser.close()

        return comments


def run_instagram_scraper_sync(post_url, max_comments=30):
    return asyncio.run(
        scrape_instagram_comments(
            post_url=post_url,
            max_comments=max_comments,
            headless=False
        )
    )