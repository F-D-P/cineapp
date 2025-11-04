from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', lambda request: redirect('account_login')),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('accounts/', include('allauth.urls')),
    path('', include('peliculas.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

