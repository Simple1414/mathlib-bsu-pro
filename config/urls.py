import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from .media import public_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('library.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
]

if settings.SERVE_MEDIA_FILES:
    # Expose only public media folders. Protected files (books/, articles/) are
    # deliberately not routable here; use the preview/download views instead.
    _media_prefix = re.escape(settings.MEDIA_URL.lstrip('/'))
    urlpatterns += [re_path(rf'^{_media_prefix}(?P<path>.+)$', public_media)]
