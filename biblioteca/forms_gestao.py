from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone

from .forms import formatar_cpf, formatar_telefone
from .models import (
    Leitor,
    NotificacaoAdmin,
    SolicitacaoFuncionario,
)


User = get_user_model()


class EdicaoCompletaUsuarioForm(forms.Form):
    NIVEIS_ACESSO = [
        ("LEITOR", "Leitor"),
        ("FUNCIONARIO", "Funcionário"),
    ]

    username = forms.CharField(
        label="Nome de usuário",
        max_length=150,
    )

    first_name = forms.CharField(
        label="Nome",
        max_length=150,
    )

    last_name = forms.CharField(
        label="Sobrenome",
        max_length=150,
    )

    email = forms.EmailField(
        label="E-mail",
    )

    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(
            attrs={
                "data-mask": "cpf",
                "inputmode": "numeric",
                "maxlength": "14",
                "placeholder": "000.000.000-00",
            }
        ),
    )

    telefone = forms.CharField(
        label="Telefone",
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "data-mask": "telefone",
                "inputmode": "numeric",
                "maxlength": "15",
                "placeholder": "(00) 00000-0000",
            }
        ),
    )

    endereco = forms.CharField(
        label="Endereço",
        max_length=255,
    )

    nivel_acesso = forms.ChoiceField(
        label="Nível de acesso",
        choices=NIVEIS_ACESSO,
    )

    tipo_vinculo = forms.ChoiceField(
        label="Tipo de vínculo",
        choices=Leitor.TIPOS_VINCULO,
    )

    ativo = forms.BooleanField(
        label="Conta ativa",
        required=False,
    )

    nova_senha = forms.CharField(
        label="Nova senha",
        required=False,
        strip=False,
        help_text=(
            "Deixe em branco para manter a senha atual."
        ),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
    )

    confirmar_senha = forms.CharField(
        label="Confirmar nova senha",
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
    )

    def __init__(
        self,
        *args,
        usuario,
        administrador,
        **kwargs,
    ):
        self.usuario = usuario
        self.administrador = administrador

        try:
            self.perfil = usuario.perfil_leitor
        except Leitor.DoesNotExist:
            self.perfil = None

        super().__init__(*args, **kwargs)

        if not self.is_bound:
            funcionario = usuario.groups.filter(
                name="Funcionarios"
            ).exists()

            self.initial.update(
                {
                    "username": usuario.username,
                    "first_name": usuario.first_name,
                    "last_name": usuario.last_name,
                    "email": usuario.email,
                    "cpf": (
                        self.perfil.cpf
                        if self.perfil
                        else ""
                    ),
                    "telefone": (
                        self.perfil.telefone
                        if self.perfil
                        else ""
                    ),
                    "endereco": (
                        self.perfil.endereco
                        if self.perfil
                        else ""
                    ),
                    "tipo_vinculo": (
                        self.perfil.tipo_vinculo
                        if self.perfil
                        else "EXTERNO"
                    ),
                    "nivel_acesso": (
                        "FUNCIONARIO"
                        if funcionario
                        else "LEITOR"
                    ),
                    "ativo": usuario.is_active,
                }
            )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if username.casefold() == "admin":
            raise forms.ValidationError(
                "O nome Admin é reservado para a conta master."
            )

        existe = (
            User.objects
            .filter(username__iexact=username)
            .exclude(pk=self.usuario.pk)
            .exists()
        )

        if existe:
            raise forms.ValidationError(
                "Este nome de usuário já está em uso."
            )

        return username

    def clean_email(self):
        email = (
            self.cleaned_data["email"]
            .strip()
            .lower()
        )

        existe_usuario = (
            User.objects
            .filter(email__iexact=email)
            .exclude(pk=self.usuario.pk)
            .exists()
        )

        if existe_usuario:
            raise forms.ValidationError(
                "Este e-mail já pertence a outra conta."
            )

        leitores = Leitor.objects.filter(
            email__iexact=email
        )

        if self.perfil:
            leitores = leitores.exclude(
                pk=self.perfil.pk
            )

        if leitores.exists():
            raise forms.ValidationError(
                "Este e-mail já pertence a outro perfil."
            )

        return email

    def clean_cpf(self):
        cpf = formatar_cpf(
            self.cleaned_data.get("cpf")
        )

        leitores = Leitor.objects.filter(cpf=cpf)

        if self.perfil:
            leitores = leitores.exclude(
                pk=self.perfil.pk
            )

        if leitores.exists():
            raise forms.ValidationError(
                "Este CPF já pertence a outro perfil."
            )

        return cpf

    def clean_telefone(self):
        return formatar_telefone(
            self.cleaned_data.get("telefone")
        )

    def clean(self):
        dados = super().clean()

        senha = dados.get("nova_senha", "")
        confirmacao = dados.get(
            "confirmar_senha",
            "",
        )

        if senha or confirmacao:
            if senha != confirmacao:
                self.add_error(
                    "confirmar_senha",
                    "As duas senhas não são iguais.",
                )

        nivel = dados.get("nivel_acesso")
        vinculo = dados.get("tipo_vinculo")

        if (
            nivel == "LEITOR"
            and vinculo == "FUNCIONARIO"
        ):
            self.add_error(
                "tipo_vinculo",
                (
                    "Uma conta de leitor não pode usar "
                    "o vínculo Funcionário."
                ),
            )

        return dados

    @transaction.atomic
    def save(self):
        usuario = self.usuario

        usuario.username = self.cleaned_data[
            "username"
        ]

        usuario.first_name = self.cleaned_data[
            "first_name"
        ]

        usuario.last_name = self.cleaned_data[
            "last_name"
        ]

        usuario.email = self.cleaned_data["email"]
        usuario.is_active = self.cleaned_data["ativo"]

        # Nenhuma conta editada pela interface vira administrador.
        usuario.is_superuser = False
        usuario.is_staff = False

        nova_senha = self.cleaned_data.get(
            "nova_senha"
        )

        if nova_senha:
            usuario.set_password(nova_senha)

        usuario.save()

        perfil, _ = Leitor.objects.get_or_create(
            usuario=usuario,
            defaults={
                "nome_completo": "",
                "cpf": self.cleaned_data["cpf"],
                "email": self.cleaned_data["email"],
                "telefone": self.cleaned_data[
                    "telefone"
                ],
                "endereco": self.cleaned_data[
                    "endereco"
                ],
                "tipo_vinculo": "EXTERNO",
                "ativo": usuario.is_active,
            },
        )

        perfil.nome_completo = (
            f"{usuario.first_name} "
            f"{usuario.last_name}"
        ).strip()

        perfil.cpf = self.cleaned_data["cpf"]
        perfil.email = self.cleaned_data["email"]
        perfil.telefone = self.cleaned_data[
            "telefone"
        ]
        perfil.endereco = self.cleaned_data[
            "endereco"
        ]
        perfil.ativo = usuario.is_active

        grupo, _ = Group.objects.get_or_create(
            name="Funcionarios"
        )

        nivel = self.cleaned_data["nivel_acesso"]

        if nivel == "FUNCIONARIO":
            perfil.tipo_vinculo = "FUNCIONARIO"
            usuario.groups.add(grupo)

            solicitacao, _ = (
                SolicitacaoFuncionario.objects
                .get_or_create(
                    usuario=usuario,
                    defaults={
                        "status": (
                            SolicitacaoFuncionario
                            .Status
                            .APROVADA
                        ),
                        "analisada_em": timezone.now(),
                        "analisada_por": (
                            self.administrador
                        ),
                    },
                )
            )

            solicitacao.status = (
                SolicitacaoFuncionario
                .Status
                .APROVADA
            )

            solicitacao.analisada_em = timezone.now()
            solicitacao.analisada_por = (
                self.administrador
            )

            solicitacao.save(
                update_fields=[
                    "status",
                    "analisada_em",
                    "analisada_por",
                ]
            )

            NotificacaoAdmin.objects.filter(
                solicitacao=solicitacao
            ).update(lida=True)

        else:
            perfil.tipo_vinculo = (
                self.cleaned_data["tipo_vinculo"]
            )

            usuario.groups.remove(grupo)

            solicitacao = (
                SolicitacaoFuncionario.objects
                .filter(usuario=usuario)
                .first()
            )

            if solicitacao:
                solicitacao.status = (
                    SolicitacaoFuncionario
                    .Status
                    .RECUSADA
                )

                solicitacao.analisada_em = (
                    timezone.now()
                )

                solicitacao.analisada_por = (
                    self.administrador
                )

                solicitacao.save(
                    update_fields=[
                        "status",
                        "analisada_em",
                        "analisada_por",
                    ]
                )

                NotificacaoAdmin.objects.filter(
                    solicitacao=solicitacao
                ).update(lida=True)

        perfil.save()

        return usuario
