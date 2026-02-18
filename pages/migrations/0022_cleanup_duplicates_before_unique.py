from django.db import migrations
from django.db.models import Count


def cleanup_articulo_destino_duplicates(apps, schema_editor):
    Rel = apps.get_model("pages", "ArticuloDestinoRelation")

    dups = (
        Rel.objects.values("articulo_id", "destino_id")
        .annotate(c=Count("id"))
        .filter(c__gt=1)
    )

    for row in dups:
        qs = (
            Rel.objects.filter(
                articulo_id=row["articulo_id"],
                destino_id=row["destino_id"],
            )
            .order_by("sort_order", "id")
        )
        keep = qs.first()
        qs.exclude(id=keep.id).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0021_alter_articulodestinorelation_options_and_more"),
    ]

    operations = [
        migrations.RunPython(cleanup_articulo_destino_duplicates, migrations.RunPython.noop),
    ]
