# Generated by Django 4.2.21 on 2025-05-24 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_servicecategory_subscriptionplan_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="login_token",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="token_expiry",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
