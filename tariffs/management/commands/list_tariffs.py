from datetime import date

from django.core.management.base import BaseCommand
from django.db.models import Q
from rich.console import Console
from rich.table import Table

from tariffs.models import Tariff


class Command(BaseCommand):
    help = "Lista as tarifas cadastradas em formato de tabela similar à ANEEL"

    def add_arguments(self, parser):
        parser.add_argument("--distributor", type=str, help="Filtrar por distribuidora (nome ou id)")
        parser.add_argument("--subgroup", type=str, help="Filtrar por subgrupo (A1, A2, A3, A4, etc.)")
        parser.add_argument("--flag", type=str, help="Filtrar por bandeira (B/G)")
        parser.add_argument("--active", action="store_true", help="Mostrar apenas tarifas ativas na data atual")
        parser.add_argument("--year", type=str, help="Filtrar por ano da vigência")

    def handle(self, *args, **options):
        console = Console()

        queryset = (
            Tariff.objects.all()
            .select_related("distributor")
            .order_by("distributor__name", "subgroup", "flag", "start_date")
        )

        if options["distributor"]:
            try:
                if options["distributor"].isdigit():
                    queryset = queryset.filter(distributor_id=options["distributor"])
                else:
                    queryset = queryset.filter(distributor__name__icontains=options["distributor"])
            except ValueError:
                queryset = queryset.filter(distributor__name__icontains=options["distributor"])

        if options["subgroup"]:
            queryset = queryset.filter(subgroup=options["subgroup"])

        if options["flag"]:
            queryset = queryset.filter(flag=options["flag"])

        if options["active"]:
            today = date.today()
            queryset = queryset.filter(start_date__lte=today, end_date__gte=today)

        if options["year"]:
            queryset = queryset.filter(Q(start_date__year=options["year"]) | Q(end_date__year=options["year"]))

        tariffs = list(queryset)

        if not tariffs:
            console.print("X [bold red]Nenhuma tarifa encontrada com os filtros especificados.[/bold red]")
            return

        console.print()
        console.print("[bold blue]Dados das Tarifas Homologadas[/bold blue]")
        console.print()
        table = self.create_aneel_style_table()

        today = date.today()
        for tariff in tariffs:
            self.add_tariff_to_aneel_table(table, tariff)

        console.print(table)
        console.print()
        console.print(f"> [green]Total: {len(tariffs)} tarifas[/green]")
        console.print()

    def create_aneel_style_table(self):
        table = Table(show_header=True, header_style="bold white on blue", border_style="dim", expand=False)

        table.add_column("Distribuidora", style="cyan", width=20)
        table.add_column("Início Vigência", width=15)
        table.add_column("Fim Vigência", width=15)
        table.add_column("Subgrupo", width=15)
        table.add_column("Modalidade", width=15)
        table.add_column("Posto", width=15)
        table.add_column("Unidade", width=10)
        table.add_column("TUSD (R$)", justify="right", width=10)
        table.add_column("TE (R$)", justify="right", width=10)
        return table

    def add_tariff_to_aneel_table(self, table, tariff):
        flag_name = "Azul" if tariff.flag == "B" else "Verde"
        posto = "Ponta" if tariff.peak_tusd_in_reais_per_kw else "Fora ponta"

        if tariff.peak_tusd_in_reais_per_kw or tariff.off_peak_tusd_in_reais_per_kw:
            unidade = "R$/kW"
            tusd_value = tariff.peak_tusd_in_reais_per_kw if posto == "Ponta" else tariff.off_peak_tusd_in_reais_per_kw
            te_value = 0.00
        else:
            unidade = "R$/MWh"
            tusd_value = (
                tariff.peak_tusd_in_reais_per_mwh if posto == "Ponta" else tariff.off_peak_tusd_in_reais_per_mwh
            )
            te_value = tariff.peak_te_in_reais_per_mwh if posto == "Ponta" else tariff.off_peak_te_in_reais_per_mwh

        tusd_formatted = f"{tusd_value:.2f}" if tusd_value else "0.00"
        te_formatted = f"{te_value:.2f}" if te_value else "0.00"

        table.add_row(
            tariff.distributor.name,
            tariff.start_date.strftime("%d/%m/%Y"),
            tariff.end_date.strftime("%d/%m/%Y"),
            tariff.subgroup,
            flag_name,
            posto,
            unidade,
            tusd_formatted,
            te_formatted,
        )

    def get_flag_name(self, flag_code):
        flag_dict = {"B": "Azul", "G": "Verde"}
        return flag_dict.get(flag_code, flag_code)
