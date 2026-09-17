from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView  # ← ADD

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',       RedirectView.as_view(url='/common/', permanent=False)),  # ← ADD
    path('common/', include('common.urls', namespace='common')),
    path('laundry/', include('laundry.urls')),
    path('restaurant/', include('restaurant.urls')),
    path('inventory/', include('inventory.urls')),
    path('financial/', include('financial.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler400 = 'errors.handlers.handler400'
handler403 = 'errors.handlers.handler403'
handler404 = 'errors.handlers.handler404'
handler500 = 'errors.handlers.handler500'