import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .twitter_scraper import run_scraper_sync
from .instagram_scraper import run_instagram_scraper_sync, force_comments_url
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .twitter_scraper import run_scraper_sync
from .instagram_scraper import run_instagram_scraper_sync, force_comments_url
from .facebook_scraper import run_facebook_scraper_sync
from .youtube_scraper import run_youtube_scraper_sync

def clean_text(text):
    if not text:
        return ""

    return " ".join(str(text).lower().strip().split())


def clean_username(username):
    if not username:
        return ""

    return str(username).lower().replace("@", "").strip()


@csrf_exempt
def check_twitter_comments(request):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Only POST request is allowed"
        })

    try:
        data = json.loads(request.body.decode("utf-8"))

        tweet_url = data.get("tweet_url")
        max_replies = data.get("max_replies", 100)
        checks = data.get("checks", [])

        if not tweet_url:
            return JsonResponse({
                "success": False,
                "message": "Tweet URL is required"
            })

        if not checks:
            return JsonResponse({
                "success": False,
                "message": "At least one username/comment check is required"
            })

        try:
            max_replies = int(max_replies)
        except:
            max_replies = 100

        if max_replies <= 0:
            max_replies = 100

        replies = run_scraper_sync(
            tweet_url=tweet_url,
            max_replies=max_replies
        )

        if not isinstance(replies, list):
            return JsonResponse({
                "success": False,
                "message": "Twitter scraper did not return a valid replies list"
            })

        results = []

        for check in checks:
            target_username = check.get("username", "")
            target_comment = check.get("comment", "")

            target_username_clean = clean_username(target_username)
            target_comment_clean = clean_text(target_comment)

            comment_found = False
            matched_comment = None

            for reply in replies:
                if not isinstance(reply, dict):
                    continue

                scraped_username = clean_username(reply.get("handle", ""))
                scraped_comment = reply.get("reply_text", "")

                scraped_comment_clean = clean_text(scraped_comment)

                username_matched = scraped_username == target_username_clean
                comment_matched = target_comment_clean in scraped_comment_clean

                if username_matched and comment_matched:
                    comment_found = True
                    matched_comment = reply
                    break

            results.append({
                "username": target_username,
                "comment": target_comment,
                "comment_found": comment_found,
                "matched_comment": matched_comment
            })

        seen_comments = []

        for reply in replies:
            if isinstance(reply, dict):
                seen_comments.append({
                    "username": reply.get("handle", ""),
                    "comment": reply.get("reply_text", "")
                })

        return JsonResponse({
            "success": True,
            "platform": "twitter",
            "post_url": tweet_url,
            "max_comments_requested": max_replies,
            "total_comments_checked": len(replies),
            "results": results,
            "seen_comments": seen_comments
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        })


@csrf_exempt
def check_instagram_comments(request):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Only POST request is allowed"
        })

    try:
        data = json.loads(request.body.decode("utf-8"))

        post_url = data.get("post_url")
        max_comments = data.get("max_comments", 30)
        checks = data.get("checks", [])

        if not post_url:
            return JsonResponse({
                "success": False,
                "message": "Instagram post URL is required"
            })

        if not checks:
            return JsonResponse({
                "success": False,
                "message": "At least one username/comment check is required"
            })

        try:
            max_comments = int(max_comments)
        except:
            max_comments = 30

        if max_comments <= 0:
            max_comments = 30

        post_url = force_comments_url(post_url)

        comments = run_instagram_scraper_sync(
            post_url=post_url,
            max_comments=max_comments
        )

        if not isinstance(comments, list):
            return JsonResponse({
                "success": False,
                "message": "Instagram scraper did not return a valid comments list"
            })

        results = []

        for check in checks:
            target_username = check.get("username", "")
            target_comment = check.get("comment", "")

            target_username_clean = clean_username(target_username)
            target_comment_clean = clean_text(target_comment)

            comment_found = False
            matched_comment = None

            for scraped in comments:
                if not isinstance(scraped, dict):
                    continue

                scraped_username = clean_username(scraped.get("username", ""))
                scraped_comment = scraped.get("comment", "")

                scraped_comment_clean = clean_text(scraped_comment)

                username_matched = scraped_username == target_username_clean
                comment_matched = target_comment_clean in scraped_comment_clean

                if username_matched and comment_matched:
                    comment_found = True
                    matched_comment = scraped
                    break

            results.append({
                "username": target_username,
                "comment": target_comment,
                "comment_found": comment_found,
                "matched_comment": matched_comment
            })

        seen_comments = []

        for scraped in comments:
            if isinstance(scraped, dict):
                seen_comments.append({
                    "username": scraped.get("username", ""),
                    "comment": scraped.get("comment", "")
                })

        return JsonResponse({
            "success": True,
            "platform": "instagram",
            "post_url": post_url,
            "max_comments_requested": max_comments,
            "total_comments_checked": len(comments),
            "results": results,
            "seen_comments": seen_comments
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        })
    


@csrf_exempt
def check_facebook_comments(request):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Only POST request is allowed"
        })

    try:
        data = json.loads(request.body.decode("utf-8"))

        post_url = data.get("post_url")
        max_comments = data.get("max_comments", 30)
        checks = data.get("checks", [])

        if not post_url:
            return JsonResponse({
                "success": False,
                "message": "Facebook post URL is required"
            })

        if not checks:
            return JsonResponse({
                "success": False,
                "message": "At least one username/comment check is required"
            })

        try:
            max_comments = int(max_comments)
        except:
            max_comments = 30

        if max_comments <= 0:
            max_comments = 30

        comments = run_facebook_scraper_sync(
            post_url=post_url,
            max_comments=max_comments
        )

        if not isinstance(comments, list):
            return JsonResponse({
                "success": False,
                "message": "Facebook scraper did not return a valid comments list"
            })

        results = []

        for check in checks:
            target_username = check.get("username", "")
            target_comment = check.get("comment", "")

            target_username_clean = clean_username(target_username)
            target_comment_clean = clean_text(target_comment)

            comment_found = False
            matched_comment = None

            for scraped in comments:
                if not isinstance(scraped, dict):
                    continue

                scraped_username = clean_username(scraped.get("username", ""))
                scraped_comment = scraped.get("comment", "")

                scraped_comment_clean = clean_text(scraped_comment)

                username_matched = scraped_username == target_username_clean
                comment_matched = target_comment_clean in scraped_comment_clean

                if username_matched and comment_matched:
                    comment_found = True
                    matched_comment = scraped
                    break

            results.append({
                "username": target_username,
                "comment": target_comment,
                "comment_found": comment_found,
                "matched_comment": matched_comment
            })

        seen_comments = []

        for scraped in comments:
            if isinstance(scraped, dict):
                seen_comments.append({
                    "username": scraped.get("username", ""),
                    "comment": scraped.get("comment", "")
                })

        return JsonResponse({
            "success": True,
            "platform": "facebook",
            "post_url": post_url,
            "max_comments_requested": max_comments,
            "total_comments_checked": len(comments),
            "results": results,
            "seen_comments": seen_comments
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        })




@csrf_exempt
def check_youtube_comments(request):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Only POST request is allowed"
        })

    try:
        data = json.loads(request.body.decode("utf-8"))

        video_url = data.get("video_url")
        max_comments = data.get("max_comments", 30)
        checks = data.get("checks", [])

        if not video_url:
            return JsonResponse({
                "success": False,
                "message": "YouTube video URL is required"
            })

        if not checks:
            return JsonResponse({
                "success": False,
                "message": "At least one username/comment check is required"
            })

        try:
            max_comments = int(max_comments)
        except:
            max_comments = 30

        if max_comments <= 0:
            max_comments = 30

        comments = run_youtube_scraper_sync(
            video_url=video_url,
            max_comments=max_comments
        )

        if not isinstance(comments, list):
            return JsonResponse({
                "success": False,
                "message": "YouTube scraper did not return a valid comments list"
            })

        results = []

        for check in checks:
            target_username = check.get("username", "")
            target_comment = check.get("comment", "")

            target_username_clean = clean_username(target_username)
            target_comment_clean = clean_text(target_comment)

            comment_found = False
            matched_comment = None

            for scraped in comments:
                if not isinstance(scraped, dict):
                    continue

                scraped_username = clean_username(scraped.get("username", ""))
                scraped_comment = scraped.get("comment", "")

                scraped_comment_clean = clean_text(scraped_comment)

                username_matched = scraped_username == target_username_clean
                comment_matched = target_comment_clean in scraped_comment_clean

                if username_matched and comment_matched:
                    comment_found = True
                    matched_comment = scraped
                    break

            results.append({
                "username": target_username,
                "comment": target_comment,
                "comment_found": comment_found,
                "matched_comment": matched_comment
            })

        seen_comments = []

        for scraped in comments:
            if isinstance(scraped, dict):
                seen_comments.append({
                    "username": scraped.get("username", ""),
                    "comment": scraped.get("comment", ""),
                    "likes": scraped.get("likes", "0"),
                    "published": scraped.get("published", "")
                })

        return JsonResponse({
            "success": True,
            "platform": "youtube",
            "post_url": video_url,
            "max_comments_requested": max_comments,
            "total_comments_checked": len(comments),
            "results": results,
            "seen_comments": seen_comments
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        })