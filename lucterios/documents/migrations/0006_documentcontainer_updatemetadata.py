# Generated by Django 3.2.16 on 2022-10-26 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0005_documentcontainer_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentcontainer',
            name='metadata',
            field=models.CharField(max_length=200, null=True, verbose_name='metadata'),
        ),
    ]
