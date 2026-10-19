import hashlib
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APIClient

from core.auditing.models import AuditEvent
from core.governance.models import DataProduct, DataProductRelease
from core.interoperability.models import FHIRExport, FHIRValidationResult


class AuditorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.users = {}
        for role in ("auditor", "admin", "data_provider", "analyst"):
            user = get_user_model().objects.create_user(username=f"test-{role}")
            user.groups.add(Group.objects.get_or_create(name=role)[0])
            self.users[role] = user
        self.product = DataProduct.objects.create(
            code="sl-district-anc-activity",
            title="Audit evidence",
            purpose="Review",
            source="test",
            data_owner=self.users["data_provider"],
            sensitivity_classification="RESTRICTED",
        )
        self.release = DataProductRelease.objects.create(
            product=self.product, version=1, schema_version="1.0.0"
        )
        self.export = FHIRExport.objects.create(
            release=self.release,
            requested_by=self.users["data_provider"],
            status="SUCCEEDED",
        )
        self.export_url = f"/api/v1/fhir-exports/{self.export.id}/"
        self.validation_url = f"{self.export_url}validations/"

    def authenticate(self, role):
        self.client.force_authenticate(user=self.users[role])

    def test_only_auditors_can_read_audit_events(self):
        AuditEvent.objects.create(
            action="TEST_EVENT", outcome="SUCCESS", correlation_id=uuid.uuid4()
        )
        for role in self.users:
            with self.subTest(role=role):
                self.authenticate(role)
                response = self.client.get("/api/v1/audit-events/")
                self.assertEqual(
                    response.status_code, 200 if role == "auditor" else 403
                )

    def test_auditor_with_multiple_groups_can_read_events(self):
        self.users["auditor"].groups.add(Group.objects.get(name="admin"))
        self.authenticate("auditor")
        self.assertEqual(self.client.get("/api/v1/audit-events/").status_code, 200)

    def test_audit_filters_use_numeric_user_ids(self):
        self.authenticate("auditor")
        event = AuditEvent.objects.create(
            actor=self.users["data_provider"],
            action="FILTER_TEST",
            outcome="SUCCESS",
            correlation_id=uuid.uuid4(),
        )
        response = self.client.get(
            "/api/v1/audit-events/",
            {
                "actor_id": self.users["data_provider"].pk,
                "action": "FILTER_TEST",
                "outcome": "SUCCESS",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["data"]["items"]], [str(event.id)]
        )
        self.assertEqual(
            self.client.get(
                "/api/v1/audit-events/", {"actor_id": "not-a-user-id"}
            ).status_code,
            400,
        )

    def test_auditor_can_read_restricted_draft_fhir_evidence(self):
        self.authenticate("auditor")
        response = self.client.get("/api/v1/fhir-exports/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            str(self.export.id), [item["id"] for item in response.data["data"]["items"]]
        )
        self.assertEqual(self.client.get(self.export_url).status_code, 200)
        self.assertEqual(self.client.get(self.validation_url).status_code, 200)

    def test_auditor_can_download_verified_bundle(self):
        self.authenticate("auditor")
        content = b'{"resourceType":"Bundle","type":"collection","entry":[]}'
        self.export.bundle_sha256 = hashlib.sha256(content).hexdigest()
        self.export.save(update_fields=["bundle_sha256"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bundle.json"
            path.write_bytes(content)
            with patch("core.interoperability.fhir_api.bundle_file", return_value=path):
                response = self.client.get(f"{self.export_url}bundle/")
                self.assertEqual(response.status_code, 200)
                # Iterate the original stream without Django's client wrapper,
                # which closes the response and TestCase's DB connection.
                self.assertEqual(b"".join(response._iterator), content)
                for closer in response._resource_closers:
                    closer()

    def test_auditor_can_queue_validation_and_view_evidence(self):
        self.authenticate("auditor")
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.validation_url)
        self.assertEqual(response.status_code, 200)
        validation_id = response.data["data"]["validationId"]
        validation = FHIRValidationResult.objects.get(pk=validation_id)
        self.assertEqual(validation.requested_by, self.users["auditor"])
        self.assertEqual(validation.status, "PENDING")
        self.assertTrue(
            AuditEvent.objects.filter(
                action="FHIR_VALIDATION_REQUESTED", resource_id=validation_id
            ).exists()
        )
        for suffix in ("", "issues/"):
            self.assertEqual(
                self.client.get(
                    f"/api/v1/fhir-validations/{validation_id}/{suffix}"
                ).status_code,
                200,
            )
        self.assertEqual(self.client.post(self.validation_url).status_code, 409)
        self.assertEqual(
            FHIRValidationResult.objects.filter(fhir_export=self.export).count(), 1
        )

    def test_validation_requires_successful_export(self):
        self.authenticate("auditor")
        self.export.status = "FAILED"
        self.export.save(update_fields=["status"])
        self.assertEqual(self.client.post(self.validation_url).status_code, 409)
        self.assertFalse(FHIRValidationResult.objects.exists())

    def test_non_auditors_cannot_trigger_validation(self):
        for role in ("admin", "data_provider", "analyst"):
            with self.subTest(role=role):
                self.authenticate(role)
                self.assertEqual(self.client.post(self.validation_url).status_code, 403)
        self.assertFalse(FHIRValidationResult.objects.exists())

    def test_auditor_cannot_generate_exports(self):
        self.authenticate("auditor")
        response = self.client.post(
            f"/api/v1/data-product-releases/{self.release.id}/fhir-exports/"
        )
        self.assertEqual(response.status_code, 403)

    def test_anonymous_access_is_denied(self):
        for path in ("/api/v1/audit-events/", self.export_url, self.validation_url):
            with self.subTest(path=path):
                self.assertIn(self.client.get(path).status_code, (401, 403))
