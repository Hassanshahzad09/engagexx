from django.db import migrations


def ensure_rating_indexes_table(apps, schema_editor):
    RatingIndexes = apps.get_model("service", "RatingIndexes")
    existing_tables = schema_editor.connection.introspection.table_names()

    if RatingIndexes._meta.db_table not in existing_tables:
        schema_editor.create_model(RatingIndexes)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("service", "0010_jobshistory_auditstatus_jobshistory_auditrevieweddate_and_more"),
    ]

    operations = [
        migrations.RunPython(ensure_rating_indexes_table, migrations.RunPython.noop),
    ]
