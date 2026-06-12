from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from biblioteca.models import Leitor, Obra


class Command(BaseCommand):
    help = (
        "Cria o administrador fixo e configura "
        "o grupo de funcionários."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        grupo, _ = Group.objects.get_or_create(
            name="Funcionarios"
        )

        tipos_conteudo = ContentType.objects.get_for_models(
            Obra,
            Leitor,
        )

        permissoes = Permission.objects.filter(
            content_type__in=tipos_conteudo.values(),
            codename__in=[
                "view_obra",
                "add_obra",
                "change_obra",
                "delete_obra",
                "view_leitor",
                "add_leitor",
                "change_leitor",
                "delete_leitor",
            ],
        )

        grupo.permissions.set(permissoes)

        administrador = User.objects.filter(
            username__iexact="Admin"
        ).first()

        if administrador is None:
            administrador = User(
                username="Admin",
            )

        administrador.username = "Admin"
        administrador.email = "admin@bibliosys.local"
        administrador.first_name = "Administrador"
        administrador.is_active = True
        administrador.is_staff = True
        administrador.is_superuser = True

        administrador.set_password("Admin")
        administrador.save()

        outros_superusuarios = User.objects.filter(
            is_superuser=True
        ).exclude(pk=administrador.pk)

        quantidade_rebaixados = (
            outros_superusuarios.count()
        )

        for usuario in outros_superusuarios:
            usuario.is_superuser = False
            usuario.is_staff = False

            usuario.save(
                update_fields=[
                    "is_superuser",
                    "is_staff",
                ]
            )

            usuario.groups.remove(grupo)

        self.stdout.write(
            self.style.SUCCESS(
                "Administrador fixo configurado."
            )
        )

        self.stdout.write(
            "Usuário: Admin"
        )

        self.stdout.write(
            "Senha: Admin"
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Grupo Funcionarios configurado."
            )
        )

        self.stdout.write(
            f"Outros superusuários rebaixados: "
            f"{quantidade_rebaixados}"
        )