# Generated by Django 3.2.9 on 2021-12-14 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('primeflix_app', '0015_auto_20211213_2346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.CharField(default=True, max_length=200, unique=True),
        ),
    ]