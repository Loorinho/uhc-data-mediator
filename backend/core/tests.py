from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from core.ingestion.models import District
from core.management.commands.seed import DISTRICT_MAPPINGS


class SeedDistrictTests(TestCase):
	def test_seed_creates_verified_districts_and_is_repeatable(self):
		call_command("seed", stdout=StringIO())
		original_ids = dict(District.objects.values_list("name", "pk"))

		call_command("seed", stdout=StringIO())

		self.assertEqual(District.objects.count(), 12)
		self.assertEqual(
			dict(District.objects.values_list("name", "pk")), original_ids
		)
		for name, uid in DISTRICT_MAPPINGS.items():
			district = District.objects.get(name=name)
			self.assertEqual(district.dhis2_org_unit_id, uid)
			self.assertEqual(district.dhis2_name, name)
			self.assertEqual(district.mapping_status, District.MappingStatus.VERIFIED)
			self.assertTrue(district.is_active)

	def test_seed_updates_existing_district_without_losing_notes(self):
		district = District.objects.create(
			name="Bo", is_active=False, mapping_notes="Existing mapping notes"
		)

		call_command("seed", stdout=StringIO())

		district.refresh_from_db()
		self.assertEqual(district.dhis2_org_unit_id, DISTRICT_MAPPINGS["Bo"])
		self.assertEqual(district.mapping_status, District.MappingStatus.VERIFIED)
		self.assertTrue(district.is_active)
		self.assertEqual(district.mapping_notes, "Existing mapping notes")
