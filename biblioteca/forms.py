import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import Leitor, Obra, SolicitacaoFuncionario


User = get_user_model()


def formatar_cpf(valor):
    numeros = re.sub(r"\D", "", valor or "")

    if len(numeros) != 11:
        raise forms.ValidationError(
            "Informe um CPF com 11 números."
        )

    return (
        f"{numeros[:3]}."
        f"{numeros[3:6]}."
        f"{numeros[6:9]}-"
        f"{numeros[9:]}"
    )


def formatar_telefone(valor):
    numeros = re.sub(r"\D", "", valor or "")

    if len(numeros) == 10:
        return (
            f"({numeros[:2]}) "
            f"{numeros[2:6]}-"
            f"{numeros[6:]}"
        )

    if len(numeros) == 11:
        return (
            f"({numeros[:2]}) "
            f"{numeros[2:7]}-"
            f"{numeros[7:]}"
        )

    raise forms.ValidationError(
        "Informe o telefone com DDD."
    )


class ObraForm(forms.ModelForm):
    class Meta:
        model = Obra

        fields = [
            "titulo",
            "autor",
            "isbn",
            "editora",
            "ano_publicacao",
            "categoria",
            "quantidade",
        ]


class LeitorForm(forms.ModelForm):
    class Meta:
        model = Leitor

        fields = [
            "nome_completo",
            "cpf",
            "email",
            "telefone",
            "endereco",
            "tipo_vinculo",
            "ativo",
        ]

        widgets = {
            "cpf": forms.TextInput(
                attrs={
                    "data-mask": "cpf",
                    "inputmode": "numeric",
                    "maxlength": "14",
                    "placeholder": "000.000.000-00",
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "data-mask": "telefone",
                    "inputmode": "numeric",
                    "maxlength": "15",
                    "placeholder": "(00) 00000-0000",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "usuario@email.com",
                }
            ),
        }

    def clean_cpf(self):
        cpf = formatar_cpf(
            self.cleaned_data.get("cpf")
        )

        consulta = Leitor.objects.filter(cpf=cpf)

        if self.instance.pk:
            consulta = consulta.exclude(
                pk=self.instance.pk
            )

        if consulta.exists():
            raise forms.ValidationError(
                "Já existe uma conta com este CPF."
            )

        return cpf

    def clean_telefone(self):
        return formatar_telefone(
            self.cleaned_data.get("telefone")
        )

    def clean_email(self):
        email = (
            self.cleaned_data.get("email", "")
            .strip()
            .lower()
        )

        consulta = Leitor.objects.filter(
            email__iexact=email
        )

        if self.instance.pk:
            consulta = consulta.exclude(
                pk=self.instance.pk
            )

        if consulta.exists():
            raise forms.ValidationError(
                "Já existe uma conta com este e-mail."
            )

        return email


class CadastroUsuarioForm(UserCreationForm):
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

    tipo_vinculo = forms.ChoiceField(
        label="Tipo de conta",
        choices=Leitor.TIPOS_VINCULO,
    )

    password1 = forms.CharField(
        label="Senha",
        strip=False,
        help_text="",
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Confirmar senha",
        strip=False,
        help_text="",
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "cpf",
            "telefone",
            "endereco",
            "tipo_vinculo",
            "password1",
            "password2",
        ]

        labels = {
            "username": "Nome de usuário",
        }

        help_texts = {
            "username": "",
        }

    def clean_username(self):
        username = (
            self.cleaned_data["username"]
            .strip()
        )

        if username.casefold() == "admin":
            raise forms.ValidationError(
                "Este nome de usuário é reservado."
            )

        if User.objects.filter(
            username__iexact=username
        ).exists():
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

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "Já existe uma conta com este e-mail."
            )

        if Leitor.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "Já existe um leitor com este e-mail."
            )

        return email

    def clean_cpf(self):
        cpf = formatar_cpf(
            self.cleaned_data.get("cpf")
        )

        if Leitor.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError(
                "Já existe uma conta com este CPF."
            )

        return cpf

    def clean_telefone(self):
        return formatar_telefone(
            self.cleaned_data.get("telefone")
        )

    @transaction.atomic
    def save(self, commit=True):
        usuario = super().save(commit=False)

        usuario.email = self.cleaned_data["email"]
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.is_active = True

        if commit:
            usuario.save()

            nome_completo = (
                f"{usuario.first_name} "
                f"{usuario.last_name}"
            ).strip()

            leitor = Leitor.objects.create(
                usuario=usuario,
                nome_completo=nome_completo,
                cpf=self.cleaned_data["cpf"],
                email=self.cleaned_data["email"],
                telefone=self.cleaned_data["telefone"],
                endereco=self.cleaned_data["endereco"],
                tipo_vinculo=self.cleaned_data[
                    "tipo_vinculo"
                ],
                ativo=True,
            )

            if leitor.tipo_vinculo == "FUNCIONARIO":
                SolicitacaoFuncionario.objects.create(
                    usuario=usuario
                )

        return usuario