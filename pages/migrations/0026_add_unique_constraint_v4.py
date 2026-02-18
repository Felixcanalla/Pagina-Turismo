from django.db import migrations, models
from django.db.models import Count

def cleanup_articulo_destino_duplicates(apps, schema_editor):
    Rel = apps.get_model("pages", "ArticuloDestinoRelation")
    dups = (
        Rel.objects.values("articulo_id", "destino_id")
        .annotate(c=Count("id"))
        .filter(c__gt=1)
    )
    for row in dups:
        ids = list(
            Rel.objects.filter(
                articulo_id=row["articulo_id"],
                destino_id=row["destino_id"],
            )
            .values_list("id", flat=True)
            .order_by("id")
        )
        Rel.objects.filter(id__in=ids[1:]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0025_remove_articulodestinorelation_unique_articulo_destino_relation_v3_and_more"),
    ]

    operations = [
        migrations.RunPython(cleanup_articulo_destino_duplicates, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="articulodestinorelation",
            constraint=models.UniqueConstraint(
                fields=("articulo", "destino"),
                name="unique_articulo_destino_relation_v4",
            ),
        ),
    ]
