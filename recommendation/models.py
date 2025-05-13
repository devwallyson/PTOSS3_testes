from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone


class Recommendation(models.Model):
    consumer_unit = models.OneToOneField("universities.ConsumerUnit", on_delete=models.CASCADE, primary_key=True)
    currentContract = models.ForeignKey("contracts.Contract", on_delete=models.CASCADE, null=True)
    isValid = models.BooleanField(null=True, blank=True)
    generatedOn = models.DateTimeField(default=timezone.now)
    energyBillsCount = models.IntegerField(null=True, blank=True)
    currentTotalCost = models.FloatField(null=True, blank=True)
    shouldRenewContract = models.BooleanField(null=True, blank=True)
    nominalSavingsPercentage = models.FloatField(null=True, blank=True)
    dates = ArrayField(models.DateField(), null=True)
    errors = models.JSONField(null=True)
    warnings = models.JSONField(null=True)
    tariffStartDate = models.DateField(null=True)
    tariffEndDate = models.DateField(null=True)
    costsComparisonPlot = models.JSONField(null=True)
    recommendedContract = models.JSONField(null=True)
    currentContractCostsPlot = models.JSONField(null=True)
    contractsComparisonTotals = models.JSONField(null=True)
    detailedContractsCostsComparisonPlot = models.JSONField(null=True)

    def __str__(self):
        return f"{self.consumer_unit} - {self.currentContract} - {self.generatedOn}"
