from rest_framework import serializers

from .models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    consumer_unit_id = serializers.IntegerField(source="consumer_unit.id", read_only=True)
    current_contract_id = serializers.IntegerField(source="currentContract.id", read_only=True)

    class Meta:
        model = Recommendation
        exclude = ["consumer_unit", "currentContract"]
