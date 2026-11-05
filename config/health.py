"""Health check endpoint for uptime monitoring and post-deploy smoke tests."""
from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.cache import never_cache


@never_cache
def healthz(request: HttpRequest) -> JsonResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:  # noqa: BLE001 - any DB failure means unhealthy
        return JsonResponse({'status': 'error', 'database': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})
