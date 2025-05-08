import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from tariffs.models import Distributor
from tariffs.services import ANEELTarifasAPI

logger = logging.getLogger("apps")


class Command(BaseCommand):
    help = "Import ANEEL distributors"

    def add_arguments(self, parser):
        parser.add_argument("-l", "--list", action="store_true", help="List distributors")
        parser.add_argument("-c", "--create", action="store_true", help="Create or update distributors")

    def handle(self, *_, **options):
        start_time = time.time()

        logger.info("------------------------[ STARTING ANEEL DISTRIBUTORS SYNC ]------------------------- ")
        resource_id = settings.RESOURCE_ID_APPROVED_TARIFFS
        base_url = settings.BASE_URL_API_ANEEL
        aneel_api = ANEELTarifasAPI(resource_id=resource_id, base_url=base_url)

        distributors = self._fetch_distributors(aneel_api)
        if options["list"]:
            self._list_distributors(distributors)
        else:
            self._create_update_distributors(distributors)

        execution_time = time.time() - start_time
        logger.info(f"Distributors sync completed in {execution_time:.2f} seconds.")
        logger.info("--------------------------------------------------------------------------------------")

    def _fetch_distributors(self, aneel_api):
        logger.info("Fetching distributors from ANEEL API...")
        distributors = aneel_api.get_active_distributors()
        total = len(distributors)
        logger.info(f"Found {total} distributors to process.")
        return distributors

    def _list_distributors(self, distributors):
        logger.info("Listing distributors...")
        if not distributors:
            logger.warning("No distributors found.")
            return

        for idx, distributor in enumerate(distributors, 1):
            logger.info(f"{idx}/{len(distributors)} {distributor['name']} | CNPJ: {distributor['cnpj']}")

    @transaction.atomic
    def _create_update_distributors(self, distributors):
        logger.info("Start creating/updating distributors.")

        success_count = 0
        error_count = 0
        created_count = 0
        updated_count = 0
        total = len(distributors)

        for idx, distributor in enumerate(distributors, 1):
            progress = f"{idx}/{total}"
            try:
                _, created = Distributor.objects.update_or_create(
                    cnpj=distributor["cnpj"],
                    defaults={
                        "name": distributor["name"],
                        "is_active": True,
                        "is_in_new_resolution": True,
                    },
                )
                if created:
                    created_count += 1
                    logger.info(f"{progress} Created new distributor: {distributor['name']}")
                else:
                    updated_count += 1
                    logger.info(f"{progress} Updated distributor: {distributor['name']}")
                success_count += 1

            except Exception as e:
                error_count += 1
                logger.error(
                    f"{progress} Error processing distributor {distributor.get('name', 'Unknown')}: {str(e)}",
                    exc_info=True,
                )

        logger.info(
            f"Sync summary: "
            f"Total: {total}, Created: {created_count}, Updated: {updated_count}, "
            f"Success: {success_count}, Failed: {error_count}"
        )

        if error_count > 0:
            logger.warning(f"[ {error_count} ] distributors failed to process!")
