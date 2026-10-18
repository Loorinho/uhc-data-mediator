from types import SimpleNamespace

from django.test import SimpleTestCase
from rest_framework import generics, serializers
from rest_framework.test import APIRequestFactory, force_authenticate

from core.shared.exploration import AuthenticatedPaginationViewMixin


class RecordSerializer(serializers.Serializer):
    id = serializers.CharField()


class RecordDetailView(AuthenticatedPaginationViewMixin, generics.RetrieveAPIView):
    serializer_class = RecordSerializer

    def get_object(self):
        return {"id": "record-id"}


class ExplorationDetailContractTests(SimpleTestCase):
    def test_authenticated_detail_uses_api_envelope(self):
        request = APIRequestFactory().get("/detail/")
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))
        response = RecordDetailView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "statusCode": 200,
                "message": "Record retrieved successfully.",
                "data": {"id": "record-id"},
            },
        )

    def test_anonymous_detail_is_denied(self):
        response = RecordDetailView.as_view()(APIRequestFactory().get("/detail/"))
        self.assertIn(response.status_code, (401, 403))
