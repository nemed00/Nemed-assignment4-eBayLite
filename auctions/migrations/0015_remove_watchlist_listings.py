# Generated by Django 4.1.2 on 2023-11-10 23:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0014_alter_watchlist_listing_alter_watchlist_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='watchlist',
            name='listings',
        ),
    ]
