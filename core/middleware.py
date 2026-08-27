from django.http import HttpResponseForbidden
from django.urls import resolve
from django.urls.exceptions import Resolver404


class ReadOnlyAdminMiddleware:
    """Prevent read-only administrators from changing data, including GET actions."""

    MUTATING_URL_PARTS = (
        'create', 'update', 'delete', 'status', 'toggle', 'convert', 'purge',
        'generate', 'approve', 'attendance', 'quick', 'edit', 'restore',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request.user, 'role', None) == 'READ_ONLY_ADMIN':
            try:
                url_name = getattr(resolve(request.path_info), 'url_name', '') or ''
            except Resolver404:
                url_name = ''
            if url_name == 'logout':
                return self.get_response(request)
            if request.method not in ('GET', 'HEAD', 'OPTIONS'):
                return HttpResponseForbidden('Read-only administrators cannot change data.')
            if any(part in url_name.lower() for part in self.MUTATING_URL_PARTS):
                return HttpResponseForbidden('Read-only administrators cannot change data.')
        return self.get_response(request)
