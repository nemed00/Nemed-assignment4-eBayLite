# Generated by Django 4.1.2 on 2023-10-30 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0012_alter_user_watchlist_watchlist_listing_watchers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='watchlist',
        ),
        migrations.AddField(
            model_name='watchlist',
            name='listings',
            field=models.ManyToManyField(related_name='watchlists', to='auctions.listing'),
        ),
    ]