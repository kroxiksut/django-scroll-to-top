from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReadingCollection",
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
                ("title", models.CharField(max_length=120, verbose_name="Title")),
                (
                    "slug",
                    models.SlugField(
                        max_length=140,
                        unique=True,
                        verbose_name="Slug",
                    ),
                ),
                ("summary", models.TextField(verbose_name="Summary")),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "sort_order",
                    models.PositiveIntegerField(default=0, verbose_name="Sort order"),
                ),
            ],
            options={
                "verbose_name": "Reading collection",
                "verbose_name_plural": "Reading collections",
                "ordering": ["sort_order", "title"],
            },
        ),
        migrations.CreateModel(
            name="ReadingEntry",
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
                ("title", models.CharField(max_length=120, verbose_name="Title")),
                ("slug", models.SlugField(max_length=140, verbose_name="Slug")),
                ("excerpt", models.TextField(verbose_name="Excerpt")),
                ("body", models.TextField(verbose_name="Body")),
                (
                    "sort_order",
                    models.PositiveIntegerField(default=0, verbose_name="Sort order"),
                ),
                (
                    "featured",
                    models.BooleanField(
                        default=False,
                        verbose_name="Featured",
                    ),
                ),
                (
                    "collection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="entries",
                        to="library.readingcollection",
                        verbose_name="Collection",
                    ),
                ),
            ],
            options={
                "verbose_name": "Reading entry",
                "verbose_name_plural": "Reading entries",
                "ordering": ["sort_order", "title"],
                "unique_together": {("collection", "slug")},
            },
        ),
    ]
