import asyncio
import json
from pathlib import Path
from django.http import JsonResponse
from playwright.async_api import async_playwright


from playwright.async_api import async_playwright
from pathlib import Path


SESSION_FILE = "twitter_session.json"
USER_DATA_DIR = "x_google_login_profile"


async def save_twitter_session():
    """
    Opens real Chrome-like persistent browser.
    Use this only one time to login with Google.
    """

    async with async_playwright() as p:

        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            channel="chrome",
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-popup-blocking",
                "--start-maximized"
            ]
        )

        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://accounts.google.com", wait_until="domcontentloaded")

        print("\nSTEP 1: Login to Google first in this browser.")
        print("After Google login completes, open x.com/login in same browser.")
        print("Then click Continue with Google.")
        print("After X/Twitter home page opens, come back to terminal.")
        input("Press Enter after Twitter/X login is fully complete: ")

        await context.storage_state(path=SESSION_FILE)

        print(f"✅ Twitter session saved successfully as {SESSION_FILE}")

        await context.close()

async def extract_replies_from_tweet(tweet_url, max_replies=100):
    """
    Opens browser visibly.
    Admin/user logs in manually if needed.
    Then scraper checks replies.
    """

    replies = []
    seen = set()

    tweet_owner = tweet_url.split("x.com/")[-1].split("/status")[0].lower().strip()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-popup-blocking"
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()

        print("Opening tweet:", tweet_url)

        await page.goto(tweet_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        print("\nIf Twitter asks for login, login manually in opened browser.")
        print("After tweet page is fully opened and replies are visible, come back here.")
        input("Press Enter to start scraping: ")

        await page.wait_for_timeout(3000)

        no_new_rounds = 0

        while len(replies) < max_replies and no_new_rounds < 20:
            old_count = len(replies)

            articles = await page.query_selector_all('article[data-testid="tweet"]')

            print(f"\nArticles found on screen: {len(articles)}")

            for article in articles:
                try:
                    text_element = await article.query_selector('div[data-testid="tweetText"]')

                    if not text_element:
                        continue

                    reply_text = await text_element.inner_text()

                    if not reply_text.strip():
                        continue

                    user_link = await article.query_selector(
                        'div[data-testid="User-Name"] a[href^="/"]'
                    )

                    if not user_link:
                        continue

                    href = await user_link.get_attribute("href")

                    if not href:
                        continue

                    handle = href.strip("/").split("/")[0].lower().strip()

                    if handle == tweet_owner:
                        print(f"Skipping original tweet owner: @{handle}")
                        continue

                    unique_key = f"{handle}:{reply_text[:100]}"

                    if unique_key in seen:
                        continue

                    seen.add(unique_key)

                    replies.append({
                        "handle": handle,
                        "reply_text": reply_text.strip()
                    })

                    print(f"Reply found: @{handle} => {reply_text[:100]}")

                    if len(replies) >= max_replies:
                        break

                except Exception as e:
                    print("Extract error:", e)
                    continue

            await page.mouse.wheel(0, 1600)
            await page.wait_for_timeout(4000)

            if len(replies) == old_count:
                no_new_rounds += 1
                print(f"No new replies found: {no_new_rounds}/20")
            else:
                no_new_rounds = 0

        await browser.close()

    print(f"\nTotal replies collected: {len(replies)}")

    return replies


def run_scraper_sync(tweet_url, max_replies=100):
    """
    Django normal view cannot directly await async function.
    So this helper runs async scraper in sync style.
    """

    return asyncio.run(
        extract_replies_from_tweet(
            tweet_url=tweet_url,
            max_replies=max_replies
        )
    )