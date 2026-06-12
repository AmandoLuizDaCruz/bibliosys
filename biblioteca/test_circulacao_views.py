from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .models import (
    Emprestimo,
    Leitor,
    NotificacaoFuncionario,
    Obra,
    Reserva,
)
from .servicos_circulacao import solicitar_obra


User = get_user_model()


class CirculacaoViewsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="Admin",
            email="admin@teste.com",
            password="Admin",
        )

        self.leitor = User.objects.create_user(
            username="leitor_tela",
            email="leitor_tela@teste.com",
            password="123",
        )

        Leitor.objects.create(
            usuario=self.leitor,
            nome_completo="Leitor da Tela",
            cpf="333.333.333-33",
            email="leitor_tela@teste.com",
            telefone="(35) 99999-3333",
            endereco="Rua do Leitor",
            tipo_vinculo="ALUNO",
            ativo=True,
        )

        self.funcionario = User.objects.create_user(
            username="funcionario_tela",
            email="funcionario_tela@teste.com",
            password="123",
        )

        Leitor.objects.create(
            usuario=self.funcionario,
            nome_completo="Funcionário da Tela",
            cpf="444.444.444-44",
            email="funcionario_tela@teste.com",
            telefone="(35) 99999-4444",
            endereco="Rua do Funcionário",
            tipo_vinculo="FUNCIONARIO",
            ativo=True,
        )

        grupo, _ = Group.objects.get_or_create(
            name="Funcionarios"
        )

        self.funcionario.groups.add(grupo)

        self.obra = Obra.objects.create(
            titulo="Livro das Views",
            autor="Autor",
            isbn="9780000000200",
            editora="Editora",
            ano_publicacao=2025,
            categoria="Teste",
            quantidade=3,
        )

    def test_leitor_reserva_pela_tela(self):
        self.client.force_login(self.leitor)

        resposta = self.client.post(
            reverse(
                "solicitar_livro",
                args=[self.obra.id],
            )
        )

        self.assertEqual(resposta.status_code, 302)

        self.assertTrue(
            Reserva.objects.filter(
                usuario=self.leitor,
                obra=self.obra,
            ).exists()
        )

    def test_funcionario_pega_livro_pela_tela(self):
        self.client.force_login(self.funcionario)

        resposta = self.client.post(
            reverse(
                "solicitar_livro",
                args=[self.obra.id],
            )
        )

        self.assertEqual(resposta.status_code, 302)

        self.assertTrue(
            Emprestimo.objects.filter(
                usuario=self.funcionario,
                status=Emprestimo.Status.ATIVO,
            ).exists()
        )

    def test_admin_nao_pode_pegar_livro(self):
        self.client.force_login(self.admin)

        self.client.post(
            reverse(
                "solicitar_livro",
                args=[self.obra.id],
            )
        )

        self.assertFalse(
            Emprestimo.objects.filter(
                usuario=self.admin
            ).exists()
        )

        self.assertFalse(
            Reserva.objects.filter(
                usuario=self.admin
            ).exists()
        )

    def test_funcionario_visualiza_notificacoes(self):
        solicitar_obra(
            self.leitor,
            self.obra,
        )

        self.client.force_login(self.funcionario)

        resposta = self.client.get(
            reverse("notificacoes_funcionarios")
        )

        self.assertEqual(resposta.status_code, 200)

        self.assertContains(
            resposta,
            "Livro das Views",
        )

        self.assertTrue(
            NotificacaoFuncionario.objects.exists()
        )

    def test_leitor_nao_acessa_notificacoes(self):
        self.client.force_login(self.leitor)

        resposta = self.client.get(
            reverse("notificacoes_funcionarios")
        )

        self.assertEqual(resposta.status_code, 302)
