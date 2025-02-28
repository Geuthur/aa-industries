from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe


def generate_button(
    corporation_id: int, template, queryset, settings, request
) -> mark_safe:
    """Generate a html button for the tax system"""
    return format_html(
        render_to_string(
            template,
            {
                "corporation_id": corporation_id,
                "queryset": queryset,
                "settings": settings,
            },
            request=request,
        )
    )
