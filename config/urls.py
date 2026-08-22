from django.contrib import admin
from django.conf import settings

from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include ('users.urls')),
    path('org/', include('organizations.urls')),
    path('projects/', include('projects.urls')),
    path('tickets/<slug:slug>/<slug:project_slug>/', include('tickets.urls')),
    path('activities/', include('activity.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )