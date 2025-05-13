import logging

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from recommendation.recommendation_utils import process_recommendation, save_recommendation
from recommendation.serializers import RecommendationSerializer
from universities.models import ConsumerUnit

from .models import Recommendation

logger = logging.getLogger("apps")


class RecommendationViewSet(ReadOnlyModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return self.queryset
        return self.queryset.filter(consumer_unit__university=user.university)

    def retrieve(self, request: Request, pk=None):
        user = self.request.user
        consumer_unit = get_object_or_404(ConsumerUnit, pk=pk)
        if consumer_unit.university != user.university and not user.is_admin:
            raise PermissionDenied()
        recommendation_instance = self._get_or_create_recommendation(consumer_unit)
        if recommendation_instance is None:
            return Response(
                {"detail": "Recommendation not found or could not be created for the specified consumer unit."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(recommendation_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_or_create_recommendation(self, consumer_unit):
        recommendation = Recommendation.objects.filter(consumer_unit=consumer_unit).first()
        if recommendation and recommendation.isValid:
            return recommendation

        try:
            processed_data, errors = process_recommendation(consumer_unit.id)
            if processed_data is None:
                logger.error(f"Failed to process recommendation data. Errors: {errors}")
                return None

            recommendation, created = save_recommendation(consumer_unit, *processed_data)
            return recommendation

        except Exception as e:
            logger.error(f"Error creating/saving new recommendation: {e}")
            return None
