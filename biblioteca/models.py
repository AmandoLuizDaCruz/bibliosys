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


class Leitor(models.Model):
    TIPOS_VINCULO = [
        ("ALUNO", "Aluno"),
        ("PROFESSOR", "Professor"),
        ("FUNCIONARIO", "Funcionário"),
        ("EXTERNO", "Público externo"),
    ]

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