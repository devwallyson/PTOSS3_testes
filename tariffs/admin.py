from django.contrib import admin

from tariffs.models import Distributor, Tariff


@admin.register(Distributor)
class DistributorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_active",
        "is_in_new_resolution",
    )
    search_fields = ("name", "state", "cnpj")
    list_filter = ("state", "is_active", "is_in_new_resolution")
    ordering = ("name", "state", "is_active")


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "distributor",
        "subgroup",
        "flag",
        "start_date",
        "end_date",
    )
    search_fields = ("distributor",)
    ordering = ("distributor", "start_date", "end_date")
    list_filter = ("distributor", "flag", "subgroup")
