# Generated by Django 3.2 on 2021-04-29 14:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_delete_usersite'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shippingadress',
            old_name='adress',
            new_name='address',
        ),
    ]
