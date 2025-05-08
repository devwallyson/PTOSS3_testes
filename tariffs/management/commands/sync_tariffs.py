import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from tariffs.models import Distributor, Tariff
from tariffs.services import ANEELTarifasAPI

logger = logging.getLogger("apps")


class Command(BaseCommand):
    help = "Import ANEEL tariffs"

    def add_arguments(self, parser):
        parser.add_argument("-a", "--is_active", action="store_true", help="Import tariffs active distributors")
        parser.add_argument("-d", "--distributor", type=str, help="Import tariffs distributor by CNPJ or name")

    def handle(self, *args, **options):
        start_time = time.time()
        logger.info("--------------------------[ STARTING ANEEL TARIFFS SYNC ]---------------------------- ")

        resource_id = settings.RESOURCE_ID_APPROVED_TARIFFS
        base_url = settings.BASE_URL_API_ANEEL
        aneel_api = ANEELTarifasAPI(resource_id=resource_id, base_url=base_url)
        logger.info(f"ENEEL API: {base_url}")
        logger.info(f"Resource ID: {resource_id}")

        queryset = Distributor.objects.all()
        if options["is_active"]:
            queryset = queryset.filter(is_active=True)
        if options["distributor"]:
            if options["distributor"].isdigit():
                queryset = queryset.filter(cnpj=options["distributor"])
            else:
                queryset = queryset.filter(name__icontains=options["distributor"])

        total = queryset.count()
        if total == 0:
            logger.warning("No distributors found in database to fetch tariffs")
            return []

        tariffs = self._fetch_tariffs(aneel_api, queryset, total)
        logger.info(f"Fetched {len(tariffs)} tariffs from in {time.time() - start_time:.2f} seconds")
        if not tariffs:
            logger.warning("No tariffs found to import")
            return
        self._create_update_tariffs(tariffs)

        execution_time = time.time() - start_time
        logger.info(f"Tariffs sync completed in {execution_time:.2f} seconds.")
        logger.info("--------------------------------------------------------------------------------------")

    def _fetch_tariffs(self, aneel_api, queryset, total):
        logger.info(f"=> Starting tariff fetch for {total} distributors...")
        success_count = 0
        error_count = 0
        empty_count = 0

        result = []
        fetch_start = time.time()
        for idx, distributor in enumerate(queryset, 1):
            log_prefix = f"[{idx}/{total}]"
            logger.info(f"{log_prefix} Fetching tariffs for distributor: {distributor.name} - {distributor.cnpj}")

            try:
                tariffs = aneel_api.get_current_tariffs_distributor(cnpj=distributor.cnpj)
                if tariffs:
                    for tariff in tariffs:
                        tariff["distributor"] = distributor
                    result.extend(tariffs)
                    success_count += 1
                else:
                    logger.warning(f"{log_prefix} No tariffs found for distributor {distributor.name}")
                    empty_count += 1
            except Exception as e:
                logger.error(f"Error fetching tariffs for distributor {distributor.name}: {str(e)}")
                error_count += 1
            time.sleep(0.1)

        fetch_duration = time.time() - fetch_start
        logger.info(
            f"Fetch summary: "
            f"Total: {total}, Success: {success_count}, Empty: {empty_count}, Errors: {error_count}, "
            f"Duration: {fetch_duration:.2f}s"
        )
        if error_count > 0:
            logger.error(f"Errors occurred while fetching tariffs for {error_count} distributors.")
        return result

    @transaction.atomic
    def _create_update_tariffs(self, tariffs):
        total = len(tariffs)
        logger.info("--------------------------------------------------------------------------------------")
        logger.info(f"=> Creating or updating {total} tariffs...")
        success_count = 0
        error_count = 0
        created_count = 0
        updated_count = 0
        processed_distributors = set()

        for idx, tariff in enumerate(tariffs, 1):
            subgroup = tariff.pop("subgroup", None)
            flag = tariff.pop("flag", None)
            distributor = tariff.pop("distributor")
            processed_distributors.add(distributor.id)

            try:
                progress = f"{idx}/{total}"
                _, created = Tariff.objects.update_or_create(
                    distributor=distributor,
                    subgroup=subgroup,
                    flag=flag,
                    defaults=tariff,
                )
                if created:
                    created_count += 1
                    logger.info(f"{progress} Created new tariff for {distributor.name}, {subgroup}, {flag}")
                else:
                    updated_count += 1
                    logger.info(f"{progress} Updated tariff for {distributor.name}, {subgroup}, {flag}")
                success_count += 1
            except Exception as e:
                error_count += 1
                logger.error(
                    f"{progress} Error processing tariff for {distributor.name}, {subgroup}, {flag}: {str(e)}",
                    exc_info=True,
                )

        logger.info(
            f"Sync summary: "
            f"Total: {total}, Created: {created_count}, Updated: {updated_count}, "
            f"Success: {success_count}, Errors: {error_count}"
        )
        if error_count > 0:
            logger.error(f"Errors occurred while processing tariffs for {error_count} distributors.")
