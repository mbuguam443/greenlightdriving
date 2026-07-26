from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from students.views import IndexView

urlpatterns = [
    path('django-admin/', admin.site.urls),
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    from django.views.static import serve as static_serve
    import os
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', static_serve, {'document_root': os.path.join(settings.BASE_DIR, 'static')}),
        re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
    ]

admin.site.site_header = 'Greenlight Driving School Admin'
admin.site.site_title = 'Greenlight Admin'
admin.site.index_title = 'Management System'
