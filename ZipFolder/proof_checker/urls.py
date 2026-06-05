from django.urls import path

from .views import (
    check_twitter_comments,
    check_instagram_comments,
    check_facebook_comments,
    check_youtube_comments,
)

urlpatterns = [
    path("check-twitter-comments/", check_twitter_comments),
    path("check-instagram-comments/", check_instagram_comments),
    path("check-facebook-comments/", check_facebook_comments),
    path("check-youtube-comments/", check_youtube_comments),
]