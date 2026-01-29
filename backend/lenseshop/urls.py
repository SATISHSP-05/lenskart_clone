
from django.contrib import admin
from django.urls import path, include
from accounts.views import logout_view
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('', include('cart.urls')),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

]

if settings.DEBUG or getattr(settings, "SERVE_MEDIA_FILES", False):
    media_url = settings.MEDIA_URL.lstrip("/")
    urlpatterns += [
        path(f"{media_url}<path:path>", serve, {"document_root": settings.MEDIA_ROOT}),
    ]


