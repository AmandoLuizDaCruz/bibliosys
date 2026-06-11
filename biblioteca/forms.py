from django import forms
from .models import Obra


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
