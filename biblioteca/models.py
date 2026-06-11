from django.db import models


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
