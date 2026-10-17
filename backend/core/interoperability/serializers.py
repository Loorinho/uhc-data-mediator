
from rest_framework import serializers


class TransformationRequestSerializer(
    serializers.Serializer
):
    productCode = serializers.SlugField(
        max_length=120,
        required=True,
    )
