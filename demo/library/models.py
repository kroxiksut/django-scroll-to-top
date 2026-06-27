from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class ReadingCollection(models.Model):
    title = models.CharField(_("Title"), max_length=120)
    slug = models.SlugField(_("Slug"), max_length=140, unique=True)
    summary = models.TextField(_("Summary"))
    notes = models.TextField(_("Notes"), blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = _("Reading collection")
        verbose_name_plural = _("Reading collections")

    def __str__(self) -> str:
        return self.title


class ReadingEntry(models.Model):
    collection = models.ForeignKey(
        ReadingCollection,
        related_name="entries",
        on_delete=models.CASCADE,
        verbose_name=_("Collection"),
    )
    title = models.CharField(_("Title"), max_length=120)
    slug = models.SlugField(_("Slug"), max_length=140)
    excerpt = models.TextField(_("Excerpt"))
    body = models.TextField(_("Body"))
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)
    featured = models.BooleanField(_("Featured"), default=False)

    class Meta:
        ordering = ["sort_order", "title"]
        unique_together = [("collection", "slug")]
        verbose_name = _("Reading entry")
        verbose_name_plural = _("Reading entries")

    def __str__(self) -> str:
        return f"{self.collection}: {self.title}"

    @property
    def paragraphs(self) -> list[str]:
        return [paragraph for paragraph in self.body.splitlines() if paragraph]
