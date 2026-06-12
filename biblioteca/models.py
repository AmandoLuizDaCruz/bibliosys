from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone


class ConfiguracaoBiblioteca(models.Model):
    prazo_emprestimo_dias = models.PositiveIntegerField(
        default=15,
        verbose_name="Prazo do empréstimo em dias",
    )

    prazo_renovacao_dias = models.PositiveIntegerField(
        default=15,
        verbose_name="Prazo adicional da renovação",
    )

    prazo_retirada_reserva_horas = models.PositiveIntegerField(
        default=24,
        verbose_name="Prazo para retirada da reserva",
    )

    limite_emprestimos_leitor = models.PositiveIntegerField(
        default=2,
    )

    limite_emprestimos_funcionario = models.PositiveIntegerField(
        default=3,
    )

    valor_multa_diaria = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("1.00"),
        verbose_name="Valor da multa por dia",
    )

    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração da biblioteca"
        verbose_name_plural = "Configurações da biblioteca"

    def save(self, *args, **kwargs):
        # Deve existir apenas uma configuração.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def carregar(cls):
        configuracao, _ = cls.objects.get_or_create(pk=1)
        return configuracao

    def __str__(self):
        return "Configurações gerais da biblioteca"


class Obra(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True)
    editora = models.CharField(max_length=150)
    ano_publicacao = models.PositiveIntegerField()
    categoria = models.CharField(max_length=100)

    quantidade = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantidade de exemplares",
    )

    def sincronizar_exemplares(self):
        """
        Cria os exemplares que ainda não existem.

        Não exclui exemplares quando a quantidade for reduzida,
        pois eles podem possuir histórico de empréstimos.
        """
        for numero in range(1, self.quantidade + 1):
            Exemplar.objects.get_or_create(
                obra=self,
                numero=numero,
            )

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
        on_delete=models.CASCADE,
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

    @property
    def funcionario_aprovado(self):
        if not self.usuario:
            return False

        return self.usuario.groups.filter(
            name="Funcionarios"
        ).exists()

    @property
    def limite_emprestimos(self):
        configuracao = ConfiguracaoBiblioteca.carregar()

        if self.funcionario_aprovado:
            return configuracao.limite_emprestimos_funcionario

        return configuracao.limite_emprestimos_leitor

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
        verbose_name = "Solicitação de funcionário"
        verbose_name_plural = "Solicitações de funcionários"

    def __str__(self):
        return (
            f"{self.usuario.username} - "
            f"{self.get_status_display()}"
        )

    def save(self, *args, **kwargs):
        nova_solicitacao = self._state.adding

        super().save(*args, **kwargs)

        if nova_solicitacao:
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

        # Funcionário não acessa o painel administrativo.
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
        verbose_name = "Notificação administrativa"
        verbose_name_plural = "Notificações administrativas"

    def __str__(self):
        return self.titulo


class Exemplar(models.Model):
    class Status(models.TextChoices):
        DISPONIVEL = "DISPONIVEL", "Disponível"
        RESERVADO = "RESERVADO", "Reservado"
        EMPRESTADO = "EMPRESTADO", "Emprestado"
        MANUTENCAO = "MANUTENCAO", "Em manutenção"
        EXTRAVIADO = "EXTRAVIADO", "Extraviado"
        BAIXADO = "BAIXADO", "Baixado"

    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name="exemplares",
    )

    numero = models.PositiveIntegerField(
        verbose_name="Número da cópia",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISPONIVEL,
    )

    somente_consulta = models.BooleanField(
        default=False,
        editable=False,
        verbose_name="Somente consulta local",
    )

    motivo_baixa = models.TextField(
        blank=True,
    )

    baixado_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["obra__titulo", "numero"]

        verbose_name = "Exemplar"
        verbose_name_plural = "Exemplares"

        constraints = [
            models.UniqueConstraint(
                fields=["obra", "numero"],
                name="exemplar_unico_por_obra_numero",
            ),
            models.CheckConstraint(
                condition=Q(numero__gte=1),
                name="numero_exemplar_maior_ou_igual_um",
            ),
            models.CheckConstraint(
                condition=~Q(
                    numero=1,
                    status__in=[
                        "RESERVADO",
                        "EMPRESTADO",
                    ],
                ),
                name="copia_um_nao_pode_circular",
            ),
        ]

    def clean(self):
        if self.numero == 1 and self.status in {
            self.Status.RESERVADO,
            self.Status.EMPRESTADO,
        }:
            raise ValidationError(
                "O exemplar número 1 é exclusivo para consulta local."
            )

    def save(self, *args, **kwargs):
        self.somente_consulta = self.numero == 1

        self.full_clean()

        super().save(*args, **kwargs)

    @property
    def pode_ser_emprestado(self):
        return (
            not self.somente_consulta
            and self.status == self.Status.DISPONIVEL
        )

    def __str__(self):
        return (
            f"{self.obra.titulo} - "
            f"Exemplar {self.numero}"
        )


class Reserva(models.Model):
    class Status(models.TextChoices):
        FILA = "FILA", "Na fila de espera"
        AGUARDANDO_RETIRADA = (
            "AGUARDANDO_RETIRADA",
            "Aguardando retirada",
        )
        RETIRADA = "RETIRADA", "Retirada"
        EXPIRADA = "EXPIRADA", "Expirada"
        CANCELADA = "CANCELADA", "Cancelada"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservas",
    )

    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name="reservas",
    )

    exemplar = models.ForeignKey(
        Exemplar,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas",
    )

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.FILA,
    )

    criada_em = models.DateTimeField(auto_now_add=True)

    disponivel_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    expira_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    finalizada_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["criada_em"]

        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"

        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "obra"],
                condition=Q(
                    status__in=[
                        "FILA",
                        "AGUARDANDO_RETIRADA",
                    ]
                ),
                name="reserva_ativa_unica_usuario_obra",
            ),
        ]

    @property
    def esta_expirada(self):
        return (
            self.status == self.Status.AGUARDANDO_RETIRADA
            and self.expira_em is not None
            and timezone.now() >= self.expira_em
        )

    @property
    def posicao_fila(self):
        if self.status != self.Status.FILA:
            return None

        return (
            Reserva.objects.filter(
                obra=self.obra,
                status=self.Status.FILA,
                criada_em__lt=self.criada_em,
            ).count()
            + 1
        )

    @transaction.atomic
    def disponibilizar_para_retirada(self, exemplar):
        if not exemplar.pode_ser_emprestado:
            raise ValidationError(
                "O exemplar selecionado não está disponível."
            )

        configuracao = ConfiguracaoBiblioteca.carregar()
        agora = timezone.now()

        exemplar.status = Exemplar.Status.RESERVADO
        exemplar.save(update_fields=["status", "somente_consulta"])

        self.exemplar = exemplar
        self.status = self.Status.AGUARDANDO_RETIRADA
        self.disponivel_em = agora
        self.expira_em = agora + timedelta(
            hours=configuracao.prazo_retirada_reserva_horas
        )

        self.save(
            update_fields=[
                "exemplar",
                "status",
                "disponivel_em",
                "expira_em",
            ]
        )

    def __str__(self):
        return (
            f"{self.usuario.username} - "
            f"{self.obra.titulo} - "
            f"{self.get_status_display()}"
        )


class Emprestimo(models.Model):
    class Status(models.TextChoices):
        ATIVO = "ATIVO", "Ativo"
        DEVOLVIDO = "DEVOLVIDO", "Devolvido"
        CANCELADO = "CANCELADO", "Cancelado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="emprestimos",
    )

    exemplar = models.ForeignKey(
        Exemplar,
        on_delete=models.PROTECT,
        related_name="emprestimos",
    )

    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emprestimo",
    )

    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emprestimos_registrados",
    )

    data_emprestimo = models.DateTimeField(
        default=timezone.now,
    )

    data_prevista_devolucao = models.DateTimeField(
        null=True,
        blank=True,
    )

    data_devolucao = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.ATIVO,
    )

    quantidade_renovacoes = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["-data_emprestimo"]

        verbose_name = "Empréstimo"
        verbose_name_plural = "Empréstimos"

        constraints = [
            models.UniqueConstraint(
                fields=["exemplar"],
                condition=Q(status="ATIVO"),
                name="um_emprestimo_ativo_por_exemplar",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.data_prevista_devolucao:
            configuracao = ConfiguracaoBiblioteca.carregar()

            self.data_prevista_devolucao = (
                self.data_emprestimo
                + timedelta(
                    days=configuracao.prazo_emprestimo_dias
                )
            )

        super().save(*args, **kwargs)

    @property
    def esta_atrasado(self):
        return (
            self.status == self.Status.ATIVO
            and timezone.now() > self.data_prevista_devolucao
        )

    @property
    def dias_atraso(self):
        data_referencia = (
            self.data_devolucao
            if self.data_devolucao
            else timezone.now()
        )

        if data_referencia <= self.data_prevista_devolucao:
            return 0

        atraso = (
            data_referencia.date()
            - self.data_prevista_devolucao.date()
        )

        return max(atraso.days, 0)

    @property
    def pode_renovar(self):
        if self.status != self.Status.ATIVO:
            return False

        if self.esta_atrasado:
            return False

        if self.quantidade_renovacoes >= 1:
            return False

        existe_fila = Reserva.objects.filter(
            obra=self.exemplar.obra,
            status__in=[
                Reserva.Status.FILA,
                Reserva.Status.AGUARDANDO_RETIRADA,
            ],
        ).exclude(usuario=self.usuario).exists()

        return not existe_fila

    def __str__(self):
        return (
            f"{self.usuario.username} - "
            f"{self.exemplar}"
        )


class Renovacao(models.Model):
    emprestimo = models.ForeignKey(
        Emprestimo,
        on_delete=models.CASCADE,
        related_name="renovacoes",
    )

    solicitada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="renovacoes_solicitadas",
    )

    data_anterior = models.DateTimeField()
    nova_data = models.DateTimeField()
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criada_em"]

        verbose_name = "Renovação"
        verbose_name_plural = "Renovações"

    def __str__(self):
        return (
            f"Renovação do empréstimo "
            f"{self.emprestimo_id}"
        )


class Multa(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        PAGA = "PAGA", "Paga"
        CANCELADA = "CANCELADA", "Cancelada"

    emprestimo = models.OneToOneField(
        Emprestimo,
        on_delete=models.CASCADE,
        related_name="multa",
    )

    dias_atraso = models.PositiveIntegerField(default=0)

    valor_diario = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDENTE,
    )

    criada_em = models.DateTimeField(auto_now_add=True)

    paga_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    registrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="multas_registradas",
    )

    class Meta:
        ordering = ["-criada_em"]

        verbose_name = "Multa"
        verbose_name_plural = "Multas"

    def recalcular(self):
        configuracao = ConfiguracaoBiblioteca.carregar()

        self.dias_atraso = self.emprestimo.dias_atraso
        self.valor_diario = configuracao.valor_multa_diaria

        self.valor_total = (
            Decimal(self.dias_atraso)
            * self.valor_diario
        )

        self.save(
            update_fields=[
                "dias_atraso",
                "valor_diario",
                "valor_total",
            ]
        )

    def __str__(self):
        return (
            f"Multa de {self.emprestimo.usuario.username} "
            f"- R$ {self.valor_total}"
        )


class NotificacaoFuncionario(models.Model):
    class Tipo(models.TextChoices):
        NOVA_RESERVA = (
            "NOVA_RESERVA",
            "Nova reserva de leitor",
        )
        LIVRO_DISPONIVEL = (
            "LIVRO_DISPONIVEL",
            "Livro disponível para retirada",
        )
        RESERVA_EXPIRADA = (
            "RESERVA_EXPIRADA",
            "Reserva expirada",
        )

    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        related_name="notificacoes_funcionarios",
    )

    tipo = models.CharField(
        max_length=25,
        choices=Tipo.choices,
        default=Tipo.NOVA_RESERVA,
    )

    titulo = models.CharField(max_length=150)
    mensagem = models.TextField()

    criada_em = models.DateTimeField(auto_now_add=True)
    ativa = models.BooleanField(default=True)

    lida_por = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="notificacoes_funcionario_lidas",
    )

    class Meta:
        ordering = ["-criada_em"]

        verbose_name = "Notificação de funcionário"
        verbose_name_plural = "Notificações de funcionários"

    def destinatarios(self):
        """
        Retorna somente funcionários aprovados.

        O administrador é removido explicitamente.
        """
        User = get_user_model()

        return User.objects.filter(
            groups__name="Funcionarios",
            is_active=True,
            is_superuser=False,
        ).distinct()

    def __str__(self):
        return self.titulo


class RegistroAuditoria(models.Model):
    class Acao(models.TextChoices):
        CADASTRO = "CADASTRO", "Cadastro"
        ALTERACAO = "ALTERACAO", "Alteração"
        EXCLUSAO = "EXCLUSAO", "Exclusão"
        LOGIN = "LOGIN", "Entrada no sistema"
        LOGOUT = "LOGOUT", "Saída do sistema"
        APROVACAO = "APROVACAO", "Aprovação"
        RECUSA = "RECUSA", "Recusa"
        RESERVA = "RESERVA", "Reserva"
        EMPRESTIMO = "EMPRESTIMO", "Empréstimo"
        RENOVACAO = "RENOVACAO", "Renovação"
        DEVOLUCAO = "DEVOLUCAO", "Devolução"
        MULTA = "MULTA", "Multa"
        BAIXA = "BAIXA", "Baixa de exemplar"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acoes_auditadas",
    )

    acao = models.CharField(
        max_length=20,
        choices=Acao.choices,
    )

    entidade = models.CharField(
        max_length=100,
    )

    objeto_id = models.CharField(
        max_length=50,
        blank=True,
    )

    descricao = models.TextField()

    dados_anteriores = models.JSONField(
        null=True,
        blank=True,
    )

    dados_novos = models.JSONField(
        null=True,
        blank=True,
    )

    endereco_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criada_em"]

        verbose_name = "Registro de auditoria"
        verbose_name_plural = "Registros de auditoria"

    @classmethod
    def registrar(
        cls,
        usuario,
        acao,
        entidade,
        descricao,
        objeto_id="",
        dados_anteriores=None,
        dados_novos=None,
        endereco_ip=None,
    ):
        return cls.objects.create(
            usuario=usuario,
            acao=acao,
            entidade=entidade,
            objeto_id=str(objeto_id),
            descricao=descricao,
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            endereco_ip=endereco_ip,
        )

    def __str__(self):
        usuario = (
            self.usuario.username
            if self.usuario
            else "Sistema"
        )

        return (
            f"{usuario} - "
            f"{self.get_acao_display()} - "
            f"{self.entidade}"
        )