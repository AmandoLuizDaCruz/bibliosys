from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from .forms import formatar_cpf, formatar_telefone
from .models import Leitor


User = get_user_model()


class EdicaoProprioPerfilForm(forms.Form):
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
        widget=forms.EmailInput(
            attrs={
                "placeholder": "usuario@email.com",
            }
        ),
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

    nova_senha = forms.CharField(
        label="Nova senha",
        required=False,
        strip=False,
        help_text="Deixe em branco para manter a senha atual.",
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
        **kwargs,
    ):
        self.usuario = usuario

        try:
            self.perfil = usuario.perfil_leitor
        except Leitor.DoesNotExist:
            self.perfil = None

        super().__init__(*args, **kwargs)

        if not self.is_bound:
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
                }
            )

    def clean_username(self):
        username = (
            self.cleaned_data["username"]
            .strip()
        )

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
                "Este nome de usuário já está sendo utilizado."
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

        leitores = Leitor.objects.filter(
            cpf=cpf
        )

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

        nova_senha = dados.get(
            "nova_senha",
            "",
        )

        confirmar_senha = dados.get(
            "confirmar_senha",
            "",
        )

        if nova_senha or confirmar_senha:
            if nova_senha != confirmar_senha:
                self.add_error(
                    "confirmar_senha",
                    "As duas senhas não são iguais.",
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

        usuario.email = self.cleaned_data[
            "email"
        ]

        nova_senha = self.cleaned_data.get(
            "nova_senha"
        )

        senha_alterada = bool(nova_senha)

        if senha_alterada:
            usuario.set_password(nova_senha)

        # Não alteramos:
        # is_active
        # is_staff
        # is_superuser
        # groups
        # user_permissions
        usuario.save()

        if self.perfil:
            perfil = self.perfil
        else:
            funcionario = usuario.groups.filter(
                name="Funcionarios"
            ).exists()

            perfil = Leitor(
                usuario=usuario,
                tipo_vinculo=(
                    "FUNCIONARIO"
                    if funcionario
                    else "EXTERNO"
                ),
                ativo=usuario.is_active,
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

        # Não alteramos:
        # tipo_vinculo
        # ativo
        perfil.save()

        return usuario, senha_alterada
