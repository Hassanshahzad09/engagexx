from django.urls import path
from .views import *

urlpatterns = [
    # 🔹 Facebook
    path('facebook/', connect_facebook),
    path('facebook/callback/', facebook_callback),

    # 🔹 Instagram
    path('instagram/', connect_instagram),
    path('instagram/callback/', instagram_callback),

    # 🔹 Twitter
    path('twitter/', connect_twitter),
    path('twitter/callback/', twitter_callback),

    # 🔹 YouTube
    path('youtube/', connect_youtube),
    path('youtube/callback/', youtube_callback),

    
]