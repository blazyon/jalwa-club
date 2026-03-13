from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.analytics import analytics_view

admin.site.site_header = "🎮 Gaming Platform Admin"
admin.site.site_title = "Gaming Platform"
admin.site.index_title = "Demo Gaming Platform Administration"

urlpatterns = [
    path('admin/analytics/', analytics_view, name='admin_analytics'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls_api')),
    path('api/wallet/', include('apps.wallet.urls_api')),
    path('api/games/wingo/', include('apps.games.wingo.urls_api')),
    path('api/games/k3/', include('apps.games.k3.urls_api')),
    path('api/games/5d/', include('apps.games.five_d.urls_api')),
    # Frontend views
    path('auth/', include('apps.users.urls')),
    path('wallet/', include('apps.wallet.urls')),
    path('games/', include('apps.games.wingo.urls')),
    path('games/k3/', include('apps.games.k3.urls')),
    path('games/5d/', include('apps.games.five_d.urls')),
    path('', include('apps.users.urls_home')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
