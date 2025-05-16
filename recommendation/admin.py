from django.contrib import admin
from django.utils.safestring import mark_safe

from recommendation.models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "consumer_unit",
        "currentContract",
        "isValid",
        "shouldRenewContract",
        "generatedOn",
    )

    search_fields = ("consumer_unit__name", "consumer_unit__code", "currentContract__name")
    ordering = ("-generatedOn",)
    list_filter = (
        "isValid",
        "shouldRenewContract",
        ("generatedOn", admin.DateFieldListFilter),
    )

    date_hierarchy = "generatedOn"

    fieldsets = (
        (
            "Informações Essenciais",
            {
                "fields": (
                    "consumer_unit",
                    "currentContract",
                    "generatedOn",
                    "isValid",
                )
            },
        ),
        (
            "Análise Contratual",
            {"fields": ("energyBillsCount", "shouldRenewContract", "formatted_savings", "formatted_comparison")},
        ),
        (
            "Detalhes Adicionais",
            {
                "classes": ("collapse",),
                "fields": (
                    "dates",
                    "errors",
                    "warnings",
                    "costsComparisonPlot",
                    "recommendedContract",
                    "currentContractCostsPlot",
                    "detailedContractsCostsComparisonPlot",
                ),
            },
        ),
    )

    readonly_fields = ("generatedOn", "formatted_savings", "formatted_comparison")

    def formatted_savings(self, obj):
        if obj.nominalSavingsPercentage is None:
            return "Não disponível"
        return f"{obj.nominalSavingsPercentage:.2f}%"

    formatted_savings.short_description = "Economia (%)"

    def formatted_comparison(self, obj):
        if not obj.contractsComparisonTotals:
            return "Não disponível"

        try:
            data = obj.contractsComparisonTotals
            total_current = data.get("totalCostInReaisInCurrent", 0)
            total_recommended = data.get("totalCostInReaisInRecommended", 0)
            demand_current = data.get("demandCostInReaisInCurrent", 0)
            demand_recommended = data.get("demandCostInReaisInRecommended", 0)
            consumption_current = data.get("consumptionCostInReaisInCurrent", 0)
            consumption_recommended = data.get("consumptionCostInReaisInRecommended", 0)

            total_diff = total_current - total_recommended
            demand_diff = demand_current - demand_recommended
            consumption_diff = consumption_current - consumption_recommended
            html = f"""
                <div style="line-height:1.5;">
                <div style="margin-bottom:12px;">
                    <strong>Demanda:</strong><br/>
                    Atual: R$ {demand_current:.2f}<br/>
                    Recomendado: R$ {demand_recommended:.2f}<br/>
                    Diferença: <span style="color:{"green" if demand_diff > 0 else "red"}">R$ {demand_diff:.2f}</span>
                </div>

                <div style="margin-bottom:12px;">
                    <strong>Consumo:</strong><br/>
                    Atual: R$ {consumption_current:.2f}<br/>
                    Recomendado: R$ {consumption_recommended:.2f}<br/>
                    Diferença: <span style="color:{"green" if consumption_diff > 0 else "red"}">
                        R$ {consumption_diff:.2f}
                    </span>
                </div>

                <div style="padding-top:5px; border-top:1px solid #eee;">
                    <strong>TOTAL:</strong><br/>
                    Atual: R$ {total_current:.2f}<br/>
                    Recomendado: R$ {total_recommended:.2f}<br/>
                    Diferença: <span style="font-weight:bold; color:{"green" if total_diff > 0 else "red"}">
                        R$ {total_diff:.2f}
                    </span>
                </div>
                </div>
            """

            return mark_safe(html)
        except Exception as e:
            return f"Erro: {str(e)}"

    formatted_comparison.short_description = "Valores Comparativos"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "contractsComparisonTotals" in form.base_fields:
            form.base_fields["contractsComparisonTotals"].widget = admin.widgets.HiddenInput()
        if "nominalSavingsPercentage" in form.base_fields:
            form.base_fields["nominalSavingsPercentage"].widget = admin.widgets.HiddenInput()
        return form
