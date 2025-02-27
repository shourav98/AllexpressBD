# Generated by Django 5.1.3 on 2024-12-01 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_alter_payment_payment_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('New', 'New'), ('Accepted', 'Accepted'), ('on the way', 'On the way'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled'), ('Shipped', 'Shipped')], default='New', max_length=10),
        ),
    ]
