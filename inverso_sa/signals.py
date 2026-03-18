from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import Usuario
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Usuario, Perfil

@receiver(post_save, sender=Usuario)
def asignar_admin_automatico(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        grupo_admin, _ = Group.objects.get_or_create(name='admin')
        instance.groups.add(grupo_admin)

        # Blindaje extra (opcional pero recomendado)
        instance.is_staff = True
        instance.save()




@receiver(post_save, sender=Usuario)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)
