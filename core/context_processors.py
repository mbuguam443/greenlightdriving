from .models import Branch, SiteSettings


def site_context(request):
    settings = SiteSettings.objects.first()
    branches = Branch.objects.filter(is_active=True)
    site_url = f'{request.scheme}://{request.get_host()}'

    context = {
        "site_name": "Greenlight Defensive Driving School",
        "site_tagline": "Drive Safe, Drive Smart",
        "phone_primary": "",
        "phone_secondary": "",
        "email": "",
        "facebook": "",
        "instagram": "",
        "twitter": "",
        "youtube": "",
        "branches": branches,
        "site_settings": settings,
        "site_url": site_url,
    }

    if settings:
        context.update(
            {
                "site_name": settings.site_name,
                "site_tagline": settings.tagline,
                "phone_primary": settings.phone_primary,
                "phone_secondary": settings.phone_secondary,
                "email": settings.email,
                "facebook": settings.facebook,
                "instagram": settings.instagram,
                "twitter": settings.twitter,
                "youtube": settings.youtube,
            }
        )

    return context
