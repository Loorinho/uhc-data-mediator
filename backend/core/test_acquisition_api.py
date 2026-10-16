from datetime import timedelta
from uuid import UUID, uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.ingestion.models import AcquisitionAttempt, Observation


class AcquisitionAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        provider_group, _ = Group.objects.get_or_create(name="data_provider")
        cls.provider = user_model.objects.create_user(username="acquisition-provider")
        cls.other_provider = user_model.objects.create_user(username="other-provider")
        cls.staff = user_model.objects.create_user(
            username="acquisition-staff", is_staff=True
        )
        cls.non_provider = user_model.objects.create_user(username="non-provider")
        for user in (cls.provider, cls.other_provider, cls.staff):
            user.groups.add(provider_group)

    def setUp(self):
        self.client.force_authenticate(user=self.provider)
        self.list_url = reverse("acquisition-list-create")

    def create_attempt(self, **kwargs):
        kwargs.setdefault("requested_by", self.provider)
        return AcquisitionAttempt.objects.create(**kwargs)

    def detail_url(self, attempt):
        return reverse("acquisition-detail", kwargs={"acquisition_id": attempt.id})

    def assert_success(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["statusCode"], status.HTTP_200_OK)
        self.assertEqual(set(response.data), {"statusCode", "message", "data"})
        return response.data["data"]

    def create_observation(self, attempt, **kwargs):
        kwargs.setdefault("indicator_id", "measure-a")
        kwargs.setdefault("org_unit_id", str(uuid4()))
        kwargs.setdefault("org_unit_name", "Alpha")
        kwargs.setdefault("period", "2025")
        kwargs.setdefault("value", "12.500000")
        kwargs.setdefault("dimensions_hash", "0" * 64)
        return Observation.objects.create(attempt=attempt, **kwargs)

    def test_list_metadata_is_distinct_sorted_and_scoped_to_owner(self):
        now = timezone.now()
        for offset, acquisition_status in enumerate(("SUCCEEDED", "PENDING", "PENDING")):
            self.create_attempt(
                status=acquisition_status,
                mode="LIVE",
                requested_at=now - timedelta(days=offset),
            )
        self.create_attempt(
            requested_by=self.other_provider, status="FAILED", mode="FIXTURE"
        )

        data = self.assert_success(self.client.get(self.list_url))

        self.assertEqual(set(data), {"items", "pagination", "statuses", "modes"})
        self.assertEqual(data["statuses"], ["PENDING", "SUCCEEDED"])
        self.assertEqual(data["modes"], ["LIVE"])
        self.assertEqual(len(data["items"]), 3)
        self.assertEqual(data["pagination"]["totalItems"], 3)

    def test_staff_metadata_and_items_include_all_owners(self):
        own = self.create_attempt(status="SUCCEEDED", mode="LIVE")
        other = self.create_attempt(
            requested_by=self.other_provider, status="FAILED", mode="FIXTURE"
        )
        self.client.force_authenticate(user=self.staff)

        data = self.assert_success(self.client.get(self.list_url))

        self.assertEqual(data["statuses"], ["FAILED", "SUCCEEDED"])
        self.assertEqual(data["modes"], ["FIXTURE", "LIVE"])
        self.assertCountEqual(
            [item["acquisitionId"] for item in data["items"]],
            [str(own.id), str(other.id)],
        )

    def test_filters_and_pagination_do_not_narrow_metadata(self):
        now = timezone.now()
        first = self.create_attempt(
            id=UUID(int=2), status="PENDING", mode="LIVE", requested_at=now
        )
        second = self.create_attempt(
            id=UUID(int=1), status="PENDING", mode="LIVE", requested_at=now
        )
        self.create_attempt(
            status="PENDING", mode="LIVE", requested_at=now - timedelta(days=1)
        )
        self.create_attempt(status="FAILED", mode="FIXTURE")
        self.create_attempt(status="FAILED", mode="LIVE")
        self.create_attempt(status="PENDING", mode="FIXTURE")
        self.create_attempt(
            requested_by=self.other_provider, status="RUNNING", mode="LIVE"
        )

        for page, expected in ((1, first), (2, second)):
            with self.subTest(page=page):
                data = self.assert_success(
                    self.client.get(
                        self.list_url,
                        {"status": "pending", "mode": "live", "page_size": 1, "page": page},
                    )
                )
                self.assertEqual(
                    [item["acquisitionId"] for item in data["items"]],
                    [str(expected.id)],
                )
                self.assertEqual(data["statuses"], ["FAILED", "PENDING"])
                self.assertEqual(data["modes"], ["FIXTURE", "LIVE"])
                self.assertEqual(
                    data["pagination"],
                    {
                        "page": page,
                        "pageSize": 1,
                        "totalItems": 3,
                        "totalPages": 3,
                        "hasNext": True,
                        "hasPrevious": page > 1,
                    },
                )

    def test_invalid_status_and_mode_return_validation_envelope(self):
        for query, message in (
            ({"status": "invalid"}, "Invalid acquisition status."),
            ({"mode": "invalid"}, "Invalid acquisition mode."),
        ):
            with self.subTest(query=query):
                response = self.client.get(self.list_url, query)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(
                    response.data,
                    {"statusCode": 400, "message": message, "data": None},
                )

    def test_empty_authorized_queryset_has_empty_metadata(self):
        self.create_attempt(
            requested_by=self.other_provider, status="FAILED", mode="FIXTURE"
        )

        data = self.assert_success(self.client.get(self.list_url))

        self.assertEqual(data["items"], [])
        self.assertEqual(data["statuses"], [])
        self.assertEqual(data["modes"], [])
        self.assertEqual(data["pagination"]["totalItems"], 0)
        self.assertFalse(data["pagination"]["hasNext"])
        self.assertFalse(data["pagination"]["hasPrevious"])

    def test_empty_filtered_result_retains_authorized_metadata(self):
        self.create_attempt(status="PENDING", mode="LIVE")

        data = self.assert_success(
            self.client.get(self.list_url, {"status": "FAILED", "mode": "FIXTURE"})
        )

        self.assertEqual(data["items"], [])
        self.assertEqual(data["pagination"]["totalItems"], 0)
        self.assertEqual(data["statuses"], ["PENDING"])
        self.assertEqual(data["modes"], ["LIVE"])

    def test_list_requires_authentication_and_data_provider_group(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.non_provider)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_uuid_detail_paginates_only_its_observations_in_stable_order(self):
        attempt = self.create_attempt(status="SUCCEEDED")
        # Insert out of order; UUID resolves ties in all preceding sort fields.
        last = self.create_observation(attempt, org_unit_name="Zulu")
        second = self.create_observation(attempt, id=UUID(int=2))
        first = self.create_observation(attempt, id=UUID(int=1))
        other = self.create_attempt(requested_by=self.other_provider)
        self.create_observation(other, org_unit_name="Aardvark")

        for page, expected in ((1, [first, second]), (2, [last])):
            with self.subTest(page=page):
                data = self.assert_success(
                    self.client.get(
                        self.detail_url(attempt), {"page_size": 2, "page": page}
                    )
                )
                self.assertEqual(data["acquisitionId"], str(attempt.id))
                self.assertEqual(
                    [item["observationId"] for item in data["observations"]["items"]],
                    [str(observation.id) for observation in expected],
                )
                self.assertEqual(
                    data["observations"]["pagination"],
                    {
                        "page": page,
                        "pageSize": 2,
                        "totalItems": 3,
                        "totalPages": 2,
                        "hasNext": page == 1,
                        "hasPrevious": page == 2,
                    },
                )

    def test_detail_raw_payload_is_opt_in_for_authorized_owner(self):
        attempt = self.create_attempt(response_payload={"rows": [["private", "12.5"]]})
        url = self.detail_url(attempt)

        for query in ({}, {"include_raw": "false"}):
            with self.subTest(query=query):
                data = self.assert_success(self.client.get(url, query))
                self.assertNotIn("responsePayload", data)
                self.assertEqual(data["observations"]["items"], [])
                self.assertEqual(data["observations"]["pagination"]["totalItems"], 0)

        data = self.assert_success(self.client.get(url, {"include_raw": "TrUe"}))
        self.assertEqual(data["responsePayload"], attempt.response_payload)

    def test_detail_and_raw_payload_are_hidden_from_other_users(self):
        attempt = self.create_attempt(
            requested_by=self.other_provider, response_payload={"secret": "other-owner"}
        )
        for query in ({}, {"include_raw": "true"}):
            with self.subTest(query=query):
                response = self.client.get(self.detail_url(attempt), query)
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
                self.assertEqual(response.data["statusCode"], 404)
                self.assertIsNone(response.data["data"])

        self.client.force_authenticate(user=self.staff)
        data = self.assert_success(
            self.client.get(self.detail_url(attempt), {"include_raw": "true"})
        )
        self.assertEqual(data["responsePayload"], attempt.response_payload)

    def test_detail_requires_authentication_and_unknown_uuid_returns_404(self):
        attempt = self.create_attempt()
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url(attempt), {"include_raw": "true"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.provider)
        response = self.client.get(
            reverse("acquisition-detail", kwargs={"acquisition_id": uuid4()})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)