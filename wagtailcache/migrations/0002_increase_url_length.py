from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wagtailcache", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="keyringitem",
            name="url",
            field=models.URLField(max_length=1000),
        ),
    ]
