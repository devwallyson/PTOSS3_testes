import logging

from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from contracts.models import Contract, EnergyBill
from recommendation.models import Recommendation

logger = logging.getLogger("apps")


@receiver(post_save, sender=Contract)
def trigger_contracts(sender, instance, created, **kwargs):
    consumer_unit = instance.consumer_unit
    logger.info(f"Contract signal: Consumer unit:={consumer_unit.id}, Contract={instance.id}, Created={created}")

    try:
        recommendation_instance = Recommendation.objects.get(consumer_unit=consumer_unit.id)
        recommendation_instance.isValid = False
        recommendation_instance.save()
        logger.info(f"Contract signal triggered for consumer unit: {consumer_unit}.")
    except Recommendation.DoesNotExist:
        logger.info(f"No recommendation found for consumer unit: {consumer_unit.id} during contract signal.")
    except Exception as e:
        logger.error(f"Error in trigger_contracts signal for consumer unit {consumer_unit.id}: {str(e)}")


@receiver([post_save, post_delete], sender=EnergyBill)
def trigger_bills(sender, instance, **kwargs):
    consumer_unit = instance.consumer_unit
    recommendation_instance = Recommendation.objects.filter(consumer_unit=consumer_unit.id).first()
    if recommendation_instance is None:
        logger.info(f"No recommendation found for consumer unit: {consumer_unit.id} during bill signal.")
        return

    logger.info(f"Energy bill signal: Consumer unit={consumer_unit.id}, Bill={instance.id}, Date={instance.date}")
    try:
        today = date.today()
        start_date = today.replace(day=1) - relativedelta(months=13)

        if instance.date >= start_date:
            logger.info(f"Energy Bill {instance.id} within analysis period. Invalidating recommendation.")
            recommendation_instance.isValid = False
            recommendation_instance.save()
        else:
            logger.info(f"Energy Bill {instance.id} outside analysis period. No action needed.")

    except Exception as e:
        logger.error(f"Error in trigger_bills: Consumer Unit={consumer_unit.id}, Energy Bill={instance.id}: {str(e)}")
