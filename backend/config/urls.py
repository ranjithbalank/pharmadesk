"""Root URLconf. API lives under /api/; the built React SPA is served at /."""
from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, HttpResponse
from django.urls import include, path, re_path


def spa_index(request):
    """Serve the React SPA's index.html for any non-API route so client-side
    routing (e.g. /billing, /inventory) works on a hard refresh. Static assets
    are served by WhiteNoise under /static/; this only handles app routes.
    """
    candidates = [
        Path(settings.STATIC_ROOT) / 'index.html',   # after collectstatic
        settings.FRONTEND_DIST / 'index.html',        # raw Vite build
    ]
    for index in candidates:
        if index.exists():
            return FileResponse(open(index, 'rb'), content_type='text/html')
    return HttpResponse(
        'PharmaDesk UI is not built yet. Run "npm run build" in frontend/ '
        'and "manage.py collectstatic", or use the Vite dev server on :5173.',
        content_type='text/plain', status=200,
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('config.api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Catch-all for the SPA — must stay last. Excludes api/admin/static/media.
urlpatterns += [
    re_path(r'^(?!api/|admin/|static/|media/).*$', spa_index),
]
