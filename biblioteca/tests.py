from django.test import TestCase
from django.urls import reverse

from .models import Leitor, Obra


class ObraCRUDTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(
            titulo="Dom Casmurro",
            autor="Machado de Assis",
            isbn="9780000000001",
            editora="Editora Teste",
            ano_publicacao=1899,
            categoria="Literatura",
            quantidade=3,
        )

    def test_listar_obras(self):
        resposta = self.client.get(reverse("listar_obras"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Dom Casmurro")

    def test_cadastrar_obra(self):
        dados = {
            "titulo": "O Cortiço",
            "autor": "Aluísio Azevedo",
            "isbn": "9780000000002",
            "editora": "Editora Teste",
            "ano_publicacao": 1890,
            "categoria": "Literatura",
            "quantidade": 2,
        }

        resposta = self.client.post(
            reverse("cadastrar_obra"),
            dados,
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(
            Obra.objects.filter(titulo="O Cortiço").exists()
        )

    def test_editar_obra(self):
        dados = {
            "titulo": "Dom Casmurro Atualizado",
            "autor": "Machado de Assis",
            "isbn": self.obra.isbn,
            "editora": self.obra.editora,
            "ano_publicacao": self.obra.ano_publicacao,
            "categoria": self.obra.categoria,
            "quantidade": 5,
        }

        resposta = self.client.post(
            reverse("editar_obra", args=[self.obra.id]),
            dados,
        )

        self.obra.refresh_from_db()

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(
            self.obra.titulo,
            "Dom Casmurro Atualizado",
        )
        self.assertEqual(self.obra.quantidade, 5)

    def test_excluir_obra(self):
        resposta = self.client.post(
            reverse("excluir_obra", args=[self.obra.id])
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(
            Obra.objects.filter(id=self.obra.id).exists()
        )


class LeitorCRUDTests(TestCase):
    def setUp(self):
        self.leitor = Leitor.objects.create(
            nome_completo="Maria da Silva",
            cpf="123.456.789-00",
            email="maria@email.com",
            telefone="35999999999",
            endereco="Rua das Flores, 100",
            tipo_vinculo="ALUNO",
            ativo=True,
        )

    def test_listar_leitores(self):
        resposta = self.client.get(reverse("listar_leitores"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Maria da Silva")

    def test_cadastrar_leitor(self):
        dados = {
            "nome_completo": "João Pereira",
            "cpf": "987.654.321-00",
            "email": "joao@email.com",
            "telefone": "35888888888",
            "endereco": "Avenida Central, 200",
            "tipo_vinculo": "PROFESSOR",
            "ativo": True,
        }

        resposta = self.client.post(
            reverse("cadastrar_leitor"),
            dados,
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(
            Leitor.objects.filter(
                email="joao@email.com"
            ).exists()
        )

    def test_editar_leitor(self):
        dados = {
            "nome_completo": "Maria da Silva Atualizada",
            "cpf": self.leitor.cpf,
            "email": self.leitor.email,
            "telefone": self.leitor.telefone,
            "endereco": self.leitor.endereco,
            "tipo_vinculo": "PROFESSOR",
            "ativo": True,
        }

        resposta = self.client.post(
            reverse("editar_leitor", args=[self.leitor.id]),
            dados,
        )

        self.leitor.refresh_from_db()

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(
            self.leitor.nome_completo,
            "Maria da Silva Atualizada",
        )
        self.assertEqual(
            self.leitor.tipo_vinculo,
            "PROFESSOR",
        )

    def test_excluir_leitor(self):
        resposta = self.client.post(
            reverse("excluir_leitor", args=[self.leitor.id])
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(
            Leitor.objects.filter(id=self.leitor.id).exists()
        )