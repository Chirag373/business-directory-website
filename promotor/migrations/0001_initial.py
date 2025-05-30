# Generated by Django 5.2.1 on 2025-05-22 18:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("businesses", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Plan",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("duration_days", models.PositiveIntegerField()),
                ("featured_listing", models.BooleanField(default=False)),
                ("priority_search", models.BooleanField(default=False)),
                ("max_images", models.PositiveIntegerField(default=5)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Coupon",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("code", models.CharField(max_length=20, unique=True)),
                ("description", models.TextField()),
                (
                    "discount_percentage",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                (
                    "discount_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("max_uses", models.PositiveIntegerField(blank=True, null=True)),
                ("current_uses", models.PositiveIntegerField(default=0)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="coupons",
                        to="businesses.business",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Promotion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                (
                    "promo_type",
                    models.CharField(
                        choices=[
                            ("banner", "Banner Ad"),
                            ("featured", "Featured Listing"),
                            ("popup", "Popup Promotion"),
                            ("email", "Email Campaign"),
                        ],
                        max_length=20,
                    ),
                ),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "image",
                    models.ImageField(blank=True, null=True, upload_to="promotions/"),
                ),
                ("link", models.URLField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("budget", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="promotions",
                        to="businesses.business",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PromotionClick",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("ip_address", models.GenericIPAddressField()),
                ("user_agent", models.TextField(blank=True, null=True)),
                ("referrer", models.URLField(blank=True, null=True)),
                (
                    "promotion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="clicks",
                        to="promotor.promotion",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("expired", "Expired"),
                            ("cancelled", "Cancelled"),
                        ],
                        max_length=20,
                    ),
                ),
                ("auto_renew", models.BooleanField(default=False)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to="businesses.business",
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to="promotor.plan",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
