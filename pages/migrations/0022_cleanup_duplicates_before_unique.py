from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0021_alter_articulodestinorelation_options_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='articulodestinorelation',
            constraint=models.UniqueConstraint(
                fields=('articulo', 'destino'),
                name='unique_articulo_destino_relation_v2',
            ),
        ),
    ]
