from django.db import migrations


def forwards(apps, schema_editor):
    table = "pages_articulopage"
    vendor = schema_editor.connection.vendor

    # Obtener columnas existentes
    with schema_editor.connection.cursor() as cursor:
        if vendor == "sqlite":
            cursor.execute(f"PRAGMA table_info({table})")
            cols = {row[1] for row in cursor.fetchall()}
        else:
            cursor.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
                [table],
            )
            cols = {row[0] for row in cursor.fetchall()}

    # Si ya existe bulk_paste, no hacemos nada
    if "bulk_paste" in cols:
        return

    # Si no existe, la creamos (SQLite/Postgres compatible)
    schema_editor.execute(
        f"ALTER TABLE {table} ADD COLUMN bulk_paste TEXT NOT NULL DEFAULT ''"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0031_alter_articulopage_body_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]