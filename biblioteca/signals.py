from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Obra


@receiver(post_save, sender=Obra)
def sincronizar_exemplares_da_obra(
    sender,
    instance,
    **kwargs,
):
    instance.sincronizar_exemplares()
