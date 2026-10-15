from rest_framework import serializers

from .models import AcquisitionAttempt


class AcquisitionRequestSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=AcquisitionAttempt.Mode.choices)