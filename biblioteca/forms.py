from django import forms

from .models import Leitor, Obra


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