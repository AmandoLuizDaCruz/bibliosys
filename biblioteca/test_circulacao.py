from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import (
    Emprestimo,
    Exemplar,
    Leitor,
    NotificacaoFuncionario,
    Obra,
    Reserva,
)
from .servicos_circulacao import (
    registrar_retirada_reserva,
    solicitar_obra,
)


User = get_user_model()


class CirculacaoTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="Admin",
            email="admin@teste.com",
            password="Admin",
        )

        self.leitor = User.objects.create_user(
            username="leitor",
            email="leitor@teste.com",
            password="123",
        )

        Leitor.objects.create(
            usuario=self.leitor,
            nome_completo="Leitor Teste",
            cpf="111.111.111-11",
            email="leitor@teste.com",
            telefone="(35) 99999-1111",
            endereco="Rua do Leitor",
            tipo_vinculo="ALUNO",
            ativo=True,
        )

        self.funcionario = User.objects.create_user(
            username="funcionario",
            email="funcionario@teste.com",
            password="123",
        )

        Leitor.objects.create(
            usuario=self.funcionario,
            nome_completo="Funcionário Teste",
            cpf="222.222.222-22",
            email="funcionario@teste.com",
            telefone="(35) 99999-2222",
            endereco="Rua do Funcionário",
            tipo_vinculo="FUNCIONARIO",
            ativo=True,
        )

        grupo, _ = Group.objects.get_or_create(
            name="Funcionarios"
        )

        self.funcionario.groups.add(grupo)

        self.obra = Obra.objects.create(
            titulo="Livro para Teste",
            autor="Autor Teste",
            isbn="9780000000100",
            editora="Editora Teste",
            ano_publicacao=2024,
            categoria="Testes",
            quantidade=3,
        )

        self.obra.sincronizar_exemplares()

    def test_exemplar_um_e_somente_consulta(self):
        exemplar = self.obra.exemplares.get(
            numero=1
        )

        self.assertTrue(
            exemplar.somente_consulta
        )

        self.assertFalse(
            exemplar.pode_ser_emprestado
        )

    def test_leitor_reserva_exemplar_dois(self):
        reserva = solicitar_obra(
            self.leitor,
            self.obra,
        )

        self.assertIsInstance(
            reserva,
            Reserva,
        )

        self.assertEqual(
            reserva.status,
            Reserva.Status.AGUARDANDO_RETIRADA,
        )

        self.assertEqual(
            reserva.exemplar.numero,
            2,
        )

        notificacao = (
            NotificacaoFuncionario.objects.get(
                reserva=reserva
            )
        )

        destinatarios = notificacao.destinatarios()

        self.assertIn(
            self.funcionario,
            destinatarios,
        )

        self.assertNotIn(
            self.admin,
            destinatarios,
        )

    def test_funcionario_recebe_livro_automaticamente(self):
        emprestimo = solicitar_obra(
            self.funcionario,
            self.obra,
        )

        self.assertIsInstance(
            emprestimo,
            Emprestimo,
        )

        self.assertEqual(
            emprestimo.status,
            Emprestimo.Status.ATIVO,
        )

        self.assertEqual(
            emprestimo.exemplar.numero,
            2,
        )

        self.assertEqual(
            emprestimo.exemplar.status,
            Exemplar.Status.EMPRESTADO,
        )

        self.assertFalse(
            NotificacaoFuncionario.objects.exists()
        )

    def test_admin_nao_pode_pegar_livro(self):
        with self.assertRaises(
            ValidationError
        ):
            solicitar_obra(
                self.admin,
                self.obra,
            )

    def test_funcionario_registra_retirada_do_leitor(self):
        reserva = solicitar_obra(
            self.leitor,
            self.obra,
        )

        emprestimo = registrar_retirada_reserva(
            self.funcionario,
            reserva,
        )

        reserva.refresh_from_db()
        emprestimo.exemplar.refresh_from_db()

        self.assertEqual(
            reserva.status,
            Reserva.Status.RETIRADA,
        )

        self.assertEqual(
            emprestimo.usuario,
            self.leitor,
        )

        self.assertEqual(
            emprestimo.registrado_por,
            self.funcionario,
        )

        self.assertEqual(
            emprestimo.exemplar.status,
            Exemplar.Status.EMPRESTADO,
        )
