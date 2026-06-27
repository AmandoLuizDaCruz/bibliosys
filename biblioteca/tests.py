from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .models import Leitor, Obra


User = get_user_model()


class ObraModelTests(TestCase):
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

    def test_criacao_obra(self):
        self.assertEqual(self.obra.titulo, "Dom Casmurro")
        self.assertEqual(self.obra.autor, "Machado de Assis")
        self.assertEqual(self.obra.isbn, "9780000000001")
        self.assertEqual(self.obra.editora, "Editora Teste")
        self.assertEqual(self.obra.ano_publicacao, 1899)
        self.assertEqual(self.obra.categoria, "Literatura")
        self.assertEqual(self.obra.quantidade, 3)

    def test_str_obra(self):
        self.assertEqual(str(self.obra), "Dom Casmurro")


class ObraCRUDTests(TestCase):
    def setUp(self):
        self.funcionario = User.objects.create_user(
            username="funcionario_teste",
            email="funcionario_teste@email.com",
            password="123",
        )

        Leitor.objects.create(
            usuario=self.funcionario,
            nome_completo="Funcionário Teste",
            cpf="555.555.555-55",
            email="funcionario_teste@email.com",
            telefone="(35) 99999-5555",
            endereco="Rua dos Testes, 10",
            tipo_vinculo="FUNCIONARIO",
            ativo=True,
        )

        grupo, _ = Group.objects.get_or_create(
            name="Funcionarios"
        )

        self.funcionario.groups.add(grupo)

        self.client.force_login(
            self.funcionario
        )

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
        resposta = self.client.get(
            reverse("listar_obras")
        )

        self.assertEqual(
            resposta.status_code,
            200,
        )

        self.assertContains(
            resposta,
            "Dom Casmurro",
        )

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

        self.assertEqual(
            resposta.status_code,
            302,
        )

        self.assertTrue(
            Obra.objects.filter(
                titulo="O Cortiço"
            ).exists()
        )

    def test_editar_obra(self):
        dados = {
            "titulo": "Dom Casmurro Atualizado",
            "autor": "Machado de Assis",
            "isbn": self.obra.isbn,
            "editora": self.obra.editora,
            "ano_publicacao": (
                self.obra.ano_publicacao
            ),
            "categoria": self.obra.categoria,
            "quantidade": 5,
        }

        resposta = self.client.post(
            reverse(
                "editar_obra",
                args=[self.obra.id],
            ),
            dados,
        )

        self.obra.refresh_from_db()

        self.assertEqual(
            resposta.status_code,
            302,
        )

        self.assertEqual(
            self.obra.titulo,
            "Dom Casmurro Atualizado",
        )

        self.assertEqual(
            self.obra.quantidade,
            5,
        )

    def test_excluir_obra(self):
        resposta = self.client.post(
            reverse(
                "excluir_obra",
                args=[self.obra.id],
            )
        )

        self.assertEqual(
            resposta.status_code,
            302,
        )

        self.assertFalse(
            Obra.objects.filter(
                id=self.obra.id
            ).exists()
        )

    def test_admin_nao_pode_cadastrar_obra(self):
        administrador = User.objects.create_superuser(
            username="Admin",
            email="admin@teste.com",
            password="Admin",
        )

        self.client.force_login(
            administrador
        )

        resposta = self.client.post(
            reverse("cadastrar_obra"),
            {
                "titulo": "Livro do Admin",
                "autor": "Autor",
                "isbn": "9780000000099",
                "editora": "Editora",
                "ano_publicacao": 2026,
                "categoria": "Teste",
                "quantidade": 2,
            },
        )

        self.assertEqual(
            resposta.status_code,
            302,
        )

        self.assertFalse(
            Obra.objects.filter(
                titulo="Livro do Admin"
            ).exists()
        )


class LeitorCRUDTests(TestCase):
    def setUp(self):
        self.administrador = User.objects.create_superuser(
            username="admin_teste",
            email="admin_teste@email.com",
            password="123",
        )

        self.client.force_login(
            self.administrador
        )

        self.leitor = Leitor.objects.create(
            nome_completo="Maria da Silva",
            cpf="123.456.789-00",
            email="maria@email.com",
            telefone="(35) 99999-9999",
            endereco="Rua das Flores, 100",
            tipo_vinculo="ALUNO",
            ativo=True,
        )

    def test_listar_leitores(self):
        resposta = self.client.get(
            reverse("listar_leitores")
        )

        self.assertEqual(
            resposta.status_code,
            200,
        )

        self.assertContains(
            resposta,
            "Maria da Silva",
        )

    def test_cadastrar_leitor(self):
        dados = {
            "nome_completo": "João Pereira",
            "cpf": "98765432100",
            "email": "joao@email.com",
            "telefone": "35888888888",
            "endereco": "Avenida Central, 200",
            "tipo_vinculo": "PROFESSOR",
            "ativo": "on",
        }

        resposta = self.client.post(
            reverse("cadastrar_leitor"),
            dados,
        )

        self.assertEqual(
            resposta.status_code,
            302,
        )

        leitor = Leitor.objects.get(
            email="joao@email.com"
        )

        self.assertEqual(
            leitor.cpf,
            "987.654.321-00",
        )

        self.assertEqual(
            leitor.telefone,
            "(35) 88888-8888",
        )

    def test_editar_leitor(self):
        dados = {
            "nome_completo": (
                "Maria da Silva Atualizada"
            ),
            "cpf": self.leitor.cpf,
            "email": self.leitor.email,
            "telefone": self.leitor.telefone,
            "endereco": self.leitor.endereco,
            "tipo_vinculo": "PROFESSOR",
            "ativo": "on",
        }

        resposta = self.client.post(
            reverse(
                "editar_leitor",
                args=[self.leitor.id],
            ),
            dados,
        )

        self.leitor.refresh_from_db()

        self.assertEqual(
            resposta.status_code,
            302,
        )

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
            reverse(
                "excluir_leitor",
                args=[self.leitor.id],
            )
        )

        self.assertEqual(
            resposta.status_code,
            302,
        )

        self.assertFalse(
            Leitor.objects.filter(
                id=self.leitor.id
            ).exists()
        )