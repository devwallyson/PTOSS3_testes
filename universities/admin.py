from django.contrib import admin
from django.utils.html import format_html

from universities.models import ConsumerUnit, University


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "acronym",
        "cnpj",
        "is_active",
        "created_on",
        "list_distributors",
    )
    search_fields = ("name", "acronym", "cnpj")
    list_filter = ("is_active", "created_on")
    ordering = ("name", "acronym", "cnpj", "is_active", "created_on")
    readonly_fields = ("created_on",)
    filter_horizontal = ("distributors",)

    def list_distributors(self, obj):
        """Lista todas as distribuidoras de uma universidade"""
        distributors = obj.distributors.all()
        if not distributors:
            return "Nenhuma distribuidora"

        html_parts = []
        for dist in distributors:
            html_parts.append(f'<a href="/admin/tariffs/distributor/{dist.id}/change/">{dist.name}</a>')

        return format_html("<br>".join(html_parts))

    list_distributors.short_description = "Distribuidoras"
    list_distributors.allow_tags = True


@admin.register(ConsumerUnit)
class ConsumerUnitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "university",
        "code",
        "name",
        "is_active",
        "total_installed_power",
        "created_on",
    )
    search_fields = ("name", "code")
    ordering = ("university", "name", "code")
    list_filter = ("university", "is_active", "created_on")
