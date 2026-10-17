from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from core.interoperability.models import CanonicalMeasure, MeasureSourceMapping


class CanonicalSeedTests(TestCase):
    def seed(self):
        output = StringIO()
        call_command("seed_canonical_measure_mapping", stdout=output)
        return output.getvalue()

    def test_creates_measure_and_source_mapping(self):
        output = self.seed()

        measure = CanonicalMeasure.objects.get(code="ANC_FIRST_VISITS")
        self.assertEqual(measure.name, "ANC first visits")
        self.assertEqual(measure.unit, CanonicalMeasure.Unit.VISITS)
        self.assertEqual(measure.aggregation_method, CanonicalMeasure.Aggregation.SUM)
        self.assertTrue(measure.is_active)
        self.assertEqual(measure.definition, {
            "category": "maternal_health",
            "geographic_grain": "district",
            "period_grain": "year_or_month",
            "is_coverage_percentage": False,
            "population_denominator": None,
        })
        mapping = MeasureSourceMapping.objects.get(
            source="DHIS2-SL-DEMO", source_measure_id="fbfJHSPpUQD"
        )
        self.assertEqual(mapping.measure, measure)
        self.assertIn("Created canonical measure: ANC_FIRST_VISITS", output)

    def test_repeated_seed_does_not_duplicate_records(self):
        self.seed()
        mapping_id = MeasureSourceMapping.objects.get().pk

        output = self.seed()

        self.assertEqual(CanonicalMeasure.objects.count(), 1)
        self.assertEqual(MeasureSourceMapping.objects.count(), 1)
        self.assertEqual(MeasureSourceMapping.objects.get().pk, mapping_id)
        self.assertIn("Updated canonical measure: ANC_FIRST_VISITS", output)

    def test_updates_existing_measure_and_mapping(self):
        self.seed()
        CanonicalMeasure.objects.filter(code="ANC_FIRST_VISITS").update(
            name="Outdated name", is_active=False, definition={}
        )
        other = CanonicalMeasure.objects.create(
            code="OTHER", name="Other", description="Unrelated measure",
            unit=CanonicalMeasure.Unit.COUNT,
            aggregation_method=CanonicalMeasure.Aggregation.NONE,
        )
        mapping = MeasureSourceMapping.objects.get()
        mapping.measure = other
        mapping.save(update_fields=["measure"])

        self.seed()

        mapping.refresh_from_db()
        self.assertEqual(mapping.measure_id, "ANC_FIRST_VISITS")
        self.assertEqual(mapping.measure.name, "ANC first visits")
        self.assertTrue(mapping.measure.is_active)
        self.assertTrue(CanonicalMeasure.objects.filter(pk="OTHER").exists())

    def test_mapping_failure_rolls_back_measure_creation(self):
        with patch(
            "core.management.commands.seed_canonical_measure_mapping."
            "MeasureSourceMapping.objects.update_or_create",
            side_effect=RuntimeError("Mapping write failed"),
        ):
            with self.assertRaisesMessage(RuntimeError, "Mapping write failed"):
                self.seed()

        self.assertFalse(CanonicalMeasure.objects.exists())
        self.assertFalse(MeasureSourceMapping.objects.exists())