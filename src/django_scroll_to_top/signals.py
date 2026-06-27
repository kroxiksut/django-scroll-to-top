from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from django_scroll_to_top.models import ScrollTopProfile, ScrollTopRevision
from django_scroll_to_top.site_config import invalidate_site_config_cache


def _invalidate_all_scopes() -> None:
    invalidate_site_config_cache(scope="site")
    invalidate_site_config_cache(scope="admin")


@receiver(post_save, sender=ScrollTopRevision)
@receiver(post_delete, sender=ScrollTopRevision)
@receiver(post_save, sender=ScrollTopProfile)
@receiver(post_delete, sender=ScrollTopProfile)
def invalidate_site_config_cache_on_change(**kwargs) -> None:
    _invalidate_all_scopes()
