import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


USER_DATA_DIR = "x_google_login_profile"


async def open_persistent_twitter_context(p):
    """
    Opens persistent browser profile.
    This keeps Google/X login saved.
    """

    try:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            channel="chrome",
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-popup-blocking",
                "--start-maximized",
            ],
        )

        return context

    except Exception as e:
        print("Chrome channel failed, using Playwright Chromium instead.")
        print("Reason:", e)

        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-popup-blocking",
                "--start-maximized",
            ],
        )

        return context


async def save_twitter_session():
    """
    One-time Twitter/X login.
    Login manually using Google.
    The session stays saved inside x_google_login_profile.
    """

    async with async_playwright() as p:
        context = await open_persistent_twitter_context(p)

        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=60000)

        print("\n" + "=" * 60)
        print("TWITTER / X LOGIN")
        print("=" * 60)
        print("1. Login manually using Google.")
        print("2. If white screen appears, type https://x.com/home manually.")
        print("3. Complete any onboarding/SSO step.")
        print("4. Wait until X home page/feed opens.")
        print("5. Come back to terminal and press Enter.")
        print("=" * 60)

        input("Press Enter ONLY after X home/feed is fully visible: ")

        await page.wait_for_timeout(3000)

        if "login" in page.url or "onboarding" in page.url or "/i/jf/" in page.url:
            await context.close()
            raise Exception(
                "Twitter/X login is still not complete. "
                "Finish login/onboarding first, then run this command again."
            )

        print("✅ Twitter/X persistent profile saved successfully.")
        print(f"Profile folder: {USER_DATA_DIR}")

        await context.close()


async def extract_replies_from_tweet(tweet_url, max_replies=100):
    """
    Uses the same persistent browser profile.
    No fresh login every time.
    """

    replies = []
    seen = set()

    tweet_owner = tweet_url.split("x.com/")[-1].split("/status")[0].lower().strip()

    async with async_playwright() as p:
        context = await open_persistent_twitter_context(p)

        page = context.pages[0] if context.pages else await context.new_page()

        print("Opening tweet:", tweet_url)

        await page.goto(tweet_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(6000)

        print("Current Twitter URL:", page.url)

        if "login" in page.url or "onboarding" in page.url or "/i/jf/" in page.url:
            print("\nTwitter/X login is not fully completed.")
            print("Complete login manually in the opened browser.")
            print("If white screen appears, manually type: https://x.com/home")
            print("After home opens, manually paste/open the tweet URL again.")
            input("Press Enter ONLY when tweet page and replies are visible: ")

            await page.wait_for_timeout(3000)

            if "login" in page.url or "onboarding" in page.url or "/i/jf/" in page.url:
                await context.close()
                raise Exception(
                    "Twitter/X is still on login/onboarding/SSO page. "
                    "Scraping cannot start until tweet page is visible."
                )

        print("\nMake sure tweet page is visible.")
        print("If replies are not visible yet, scroll manually a little.")
        input("Press Enter to start scraping replies: ")

        await page.wait_for_timeout(3000)

        # Move below original tweet
        for _ in range(3):
            await page.mouse.wheel(0, 1200)
            await page.wait_for_timeout(2500)

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

                    bad_handles = [
                        "home",
                        "explore",
                        "notifications",
                        "messages",
                        "settings",
                    ]

                    if handle in bad_handles:
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

        await context.close()

    print(f"\nTotal replies collected: {len(replies)}")

    return replies


def run_scraper_sync(tweet_url, max_replies=100):
    return asyncio.run(
        extract_replies_from_tweet(
            tweet_url=tweet_url,
            max_replies=max_replies
        )
    )