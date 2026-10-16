from django.db import migrations


class Migration(migrations.Migration):
    """Destructive reset before rebuilding ingestion tables with UUID keys.

    Existing ingestion records are intentionally discarded. User and
    authentication tables are not affected.
    """

    dependencies = [
        ("core", "0005_district_districtpopulation_observation_and_more"),
    ]

    operations = [
        migrations.DeleteModel(name="Observation"),
        migrations.DeleteModel(name="DistrictPopulation"),
        migrations.DeleteModel(name="District"),
        migrations.DeleteModel(name="AcquisitionAttempt"),
    ]