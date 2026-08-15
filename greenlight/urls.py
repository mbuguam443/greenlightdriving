from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve
from students.views import IndexView
from student_portal.views import pwa_manifest, pwa_service_worker
import os

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # PWA install support (service worker must be at root scope)
    path('manifest.webmanifest', pwa_manifest, name='pwa_manifest'),
    path('sw.js', pwa_service_worker, name='pwa_sw'),

    # Media files — serve via Django BEFORE includes swallow the URL
    re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': str(settings.MEDIA_ROOT)}),

    # Static files — serve via Django (Apache also handles /static/ via .htaccess)
    re_path(r'^static/(?P<path>.*)$', static_serve, {'document_root': os.path.join(str(settings.BASE_DIR), 'static')}),

    path('', include('website.urls')),
    path('accounts/', include('accounts.urls')),
    path('core/', include('core.urls')),
    path('admissions/', include('admissions.urls')),
    path('dashboard/', IndexView.as_view(), name='dashboard'),
    path('students/', include('students.urls', namespace='students')),
    path('payments/', include('payments.urls')),
    path('lessons/', include('lessons.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('instructors/', include('instructors.urls')),
    path('ntsa/', include('ntsa.urls')),
    path('reports/', include('reports.urls')),
    path('portal/', include('student_portal.urls')),
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = 'Greenlight Driving School Admin'
admin.site.site_title = 'Greenlight Admin'
admin.site.index_title = 'Management System'
