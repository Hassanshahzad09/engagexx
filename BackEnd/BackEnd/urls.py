from django.contrib import admin
from django.urls import include, path

#from .views import check_login, connect_facebook, connect_instagram, facebook_callback,connect_instagram, instagram_callback, login_view, logout_view,twitter_callback, connect_twitter, connect_youtube, youtube_callback, google_login, google_callback,connections_status,disconnect_platform

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('service.urls')),
    path('ml/', include('mlservice.urls')),
    path('oauth/',include('social_auth.urls'))
]