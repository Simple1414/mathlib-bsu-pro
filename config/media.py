"""Serving of public media files (covers, avatars) without exposing protected uploads."""
import posixpath

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.views.static import serve


def public_media(request: HttpRequest, path: str) -> HttpResponse:
    """Serve a file from MEDIA_ROOT only if it lives in a PUBLIC_MEDIA_DIRS folder.

    The path is normalized first, so traversal such as ``covers/../books/x.pdf``
    resolves to ``books/x.pdf`` and is rejected.
    """
    normalized = posixpath.normpath(path).lstrip('/')
    top_level = normalized.split('/', 1)[0]
    if '/' not in normalized or top_level not in settings.PUBLIC_MEDIA_DIRS:
        raise Http404('Файл ёфт нашуд.')
    return serve(request, normalized, document_root=settings.MEDIA_ROOT)
