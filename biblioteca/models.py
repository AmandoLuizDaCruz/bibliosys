from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models, transaction
from django.utils import timezone


class Obra(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True)
    editora = models.CharField(max_length=150)
    ano_publicacao = models.PositiveIntegerField()
    categoria = models.CharField(max_length=100)
    quantidade = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.titulo


class Leitor(models.Model):
    TIPOS_VINCULO = [
        ("ALUNO", "Aluno"),
        ("PROFESSOR", "Professor"),
        ("FUNCIONARIO", "Funcionário"),
        ("EXTERNO", "Público externo"),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="perfil_leitor",
    )

    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20)
    endereco = models.CharField(max_length=255)

    tipo_vinculo = models.CharField(
        max_length=20,
        choices=TIPOS_VINCULO,
    )

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome_completo


class SolicitacaoFuncionario(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        APROVADA = "APROVADA", "Aprovada"
        RECUSADA = "RECUSADA", "Recusada"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="solicitacao_funcionario",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDENTE,
    )

    criada_em = models.DateTimeField(auto_now_add=True)
    analisada_em = models.DateTimeField(null=True, blank=True)

    analisada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitacoes_analisadas",
    )

    class Meta:
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.usuario.username} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        nova = self._state.adding

        super().save(*args, **kwargs)

        if nova:
            NotificacaoAdmin.objects.get_or_create(
                solicitacao=self,
                defaults={
                    "titulo": "Nova solicitação de funcionário",
                    "mensagem": (
                        f"O usuário {self.usuario.username} "
                        "solicitou acesso como funcionário."
                    ),
                },
            )

    @transaction.atomic
    def aprovar(self, administrador):
        grupo, _ = Group.objects.get_or_create(
            name="Funcionarios"
        )

        # Funcionário não entra no painel administrativo.
        self.usuario.is_staff = False
        self.usuario.is_superuser = False
        self.usuario.is_active = True

        self.usuario.save(
            update_fields=[
                "is_staff",
                "is_superuser",
                "is_active",
            ]
        )

        self.usuario.groups.add(grupo)

        self.status = self.Status.APROVADA
        self.analisada_em = timezone.now()
        self.analisada_por = administrador

        self.save(
            update_fields=[
                "status",
                "analisada_em",
                "analisada_por",
            ]
        )

        NotificacaoAdmin.objects.filter(
            solicitacao=self
        ).update(lida=True)

    @transaction.atomic
    def recusar(self, administrador):
        grupo = Group.objects.filter(
            name="Funcionarios"
        ).first()

        self.usuario.is_staff = False
        self.usuario.is_superuser = False

        self.usuario.save(
            update_fields=[
                "is_staff",
                "is_superuser",
            ]
        )

        if grupo:
            self.usuario.groups.remove(grupo)

        self.status = self.Status.RECUSADA
        self.analisada_em = timezone.now()
        self.analisada_por = administrador

        self.save(
            update_fields=[
                "status",
                "analisada_em",
                "analisada_por",
            ]
        )

        NotificacaoAdmin.objects.filter(
            solicitacao=self
        ).update(lida=True)


class NotificacaoAdmin(models.Model):
    solicitacao = models.OneToOneField(
        SolicitacaoFuncionario,
        on_delete=models.CASCADE,
        related_name="notificacao",
    )

    titulo = models.CharField(max_length=150)
    mensagem = models.TextField()
    criada_em = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)

    class Meta:
        ordering = ["lida", "-criada_em"]

    def __str__(self):
        return self.titulo