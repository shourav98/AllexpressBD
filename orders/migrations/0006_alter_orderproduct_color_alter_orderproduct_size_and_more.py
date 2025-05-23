# Generated by Django 5.1.3 on 2025-04-11 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_alter_order_status'),
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderproduct',
            name='color',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='size',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.RemoveField(
            model_name='orderproduct',
            name='variations',
        ),
        migrations.AddField(
            model_name='orderproduct',
            name='variations',
            field=models.ManyToManyField(blank=True, to='store.variation'),
        ),
    ]
