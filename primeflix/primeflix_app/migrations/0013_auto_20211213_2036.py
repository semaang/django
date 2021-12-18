# Generated by Django 3.2.9 on 2021-12-13 19:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('primeflix_app', '0012_alter_product_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255)),
            ],
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ('-created',)},
        ),
        migrations.RemoveField(
            model_name='product',
            name='active',
        ),
        migrations.RemoveField(
            model_name='product',
            name='platform',
        ),
        migrations.AddField(
            model_name='customer',
            name='stripe_customer_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='created_by',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='auth.user'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='in_stock',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='producer',
            field=models.CharField(default='admin', max_length=255),
        ),
        migrations.AddField(
            model_name='product',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4),
        ),
        migrations.AlterField(
            model_name='product',
            name='title',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.DeleteModel(
            name='StreamPlatformList',
        ),
        migrations.AddField(
            model_name='product',
            name='Category',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='primeflix_app.category'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='Theme',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='primeflix_app.theme'),
            preserve_default=False,
        ),
    ]