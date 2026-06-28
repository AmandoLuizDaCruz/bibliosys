from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import Leitor, Obra, Exemplar, Emprestimo, Reserva, Multa


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


class LeitorModelTests(TestCase):
    def setUp(self):
        self.leitor = Leitor.objects.create(
            nome_completo="João Silva",
            cpf="123.456.789-00",
            email="joao@email.com",
            telefone="(35) 99999-9999",
            endereco="Rua das Flores, 100",
            tipo_vinculo="ALUNO",
            ativo=True,
        )

    def test_criacao_leitor(self):
        self.assertEqual(self.leitor.nome_completo, "João Silva")
        self.assertEqual(self.leitor.cpf, "123.456.789-00")
        self.assertEqual(self.leitor.email, "joao@email.com")
        self.assertEqual(self.leitor.telefone, "(35) 99999-9999")
        self.assertEqual(self.leitor.endereco, "Rua das Flores, 100")
        self.assertEqual(self.leitor.tipo_vinculo, "ALUNO")
        self.assertTrue(self.leitor.ativo)

    def test_str_leitor(self):
        self.assertEqual(str(self.leitor), "João Silva")


class ExemplarModelTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(
            titulo="1984",
            autor="George Orwell",
            isbn="9780451524935",
            editora="Signet",
            ano_publicacao=1949,
            categoria="Ficção Científica",
            quantidade=2,
        )
        self.obra.sincronizar_exemplares()
        self.exemplar = self.obra.exemplares.first()

    def test_criacao_exemplar(self):
        self.assertEqual(self.exemplar.obra, self.obra)
        self.assertIsNotNone(self.exemplar.numero)
        self.assertEqual(
            self.exemplar.status,
            Exemplar.Status.DISPONIVEL,
        )
        self.assertTrue(self.exemplar.somente_consulta)

    def test_str_exemplar(self):
        self.assertIn("1984", str(self.exemplar))
        self.assertIn("Exemplar 1", str(self.exemplar))


class EmprestimoModelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="leitor_teste",
            email="leitor@email.com",
            password="senha123",
        )
        self.obra = Obra.objects.create(
            titulo="O Senhor dos Anéis",
            autor="J.R.R. Tolkien",
            isbn="9780544003415",
            editora="Houghton Mifflin",
            ano_publicacao=1954,
            categoria="Fantasia",
            quantidade=2,
        )
        self.obra.sincronizar_exemplares()
        self.exemplar = self.obra.exemplares.last()
        self.emprestimo = Emprestimo.objects.create(
            usuario=self.usuario,
            exemplar=self.exemplar,
        )

    def test_criacao_emprestimo(self):
        self.assertEqual(self.emprestimo.usuario, self.usuario)
        self.assertEqual(self.emprestimo.exemplar, self.exemplar)
        self.assertEqual(
            self.emprestimo.status,
            Emprestimo.Status.ATIVO,
        )
        self.assertEqual(self.emprestimo.quantidade_renovacoes, 0)
        self.assertIsNotNone(self.emprestimo.data_emprestimo)
        self.assertIsNotNone(self.emprestimo.data_prevista_devolucao)

    def test_str_emprestimo(self):
        self.assertIn("leitor_teste", str(self.emprestimo))
        self.assertIn("O Senhor dos Anéis", str(self.emprestimo))


class ReservaModelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="leitor_reserva",
            email="leitor_reserva@email.com",
            password="senha123",
        )
        self.obra = Obra.objects.create(
            titulo="O Hobbit",
            autor="J.R.R. Tolkien",
            isbn="9780547928227",
            editora="Houghton Mifflin",
            ano_publicacao=1937,
            categoria="Fantasia",
            quantidade=1,
        )
        self.reserva = Reserva.objects.create(
            usuario=self.usuario,
            obra=self.obra,
        )

    def test_criacao_reserva(self):
        self.assertEqual(self.reserva.usuario, self.usuario)
        self.assertEqual(self.reserva.obra, self.obra)
        self.assertEqual(self.reserva.status, Reserva.Status.FILA)
        self.assertIsNone(self.reserva.exemplar)
        self.assertIsNotNone(self.reserva.criada_em)

    def test_str_reserva(self):
        esperado = (
            f"leitor_reserva - O Hobbit - {self.reserva.get_status_display()}"
        )
        self.assertEqual(str(self.reserva), esperado)


class MultaModelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="leitor_multa",
            email="leitor_multa@email.com",
            password="senha123",
        )
        self.obra = Obra.objects.create(
            titulo="Harry Potter e a Pedra Filosofal",
            autor="J.K. Rowling",
            isbn="9780747532699",
            editora="Bloomsbury",
            ano_publicacao=1997,
            categoria="Fantasia",
            quantidade=2,
        )
        self.obra.sincronizar_exemplares()
        self.exemplar = self.obra.exemplares.last()
        self.emprestimo = Emprestimo.objects.create(
            usuario=self.usuario,
            exemplar=self.exemplar,
        )
        self.multa = Multa.objects.create(
            emprestimo=self.emprestimo,
            dias_atraso=5,
            valor_diario="1.50",
            valor_total="7.50",
        )

    def test_criacao_multa(self):
        self.assertEqual(self.multa.emprestimo, self.emprestimo)
        self.assertEqual(self.multa.dias_atraso, 5)
        self.assertEqual(str(self.multa.valor_diario), "1.50")
        self.assertEqual(str(self.multa.valor_total), "7.50")
        self.assertEqual(self.multa.status, Multa.Status.PENDENTE)
        self.assertIsNotNone(self.multa.criada_em)

    def test_str_multa(self):
        esperado = f"Multa de leitor_multa - R$ 7.50"
        self.assertEqual(str(self.multa), esperado)


class RottasListagemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username="admin_listagem",
            email="admin_listagem@email.com",
            password="senha123",
        )
        self.leitor = User.objects.create_user(
            username="leitor_listagem",
            email="leitor_listagem@email.com",
            password="senha123",
        )
        Leitor.objects.create(
            usuario=self.leitor,
            nome_completo="Leitor Teste",
            cpf="111.111.111-11",
            email="leitor_listagem@email.com",
            telefone="(35) 99999-9999",
            endereco="Rua Teste, 1",
            tipo_vinculo="ALUNO",
            ativo=True,
        )
        self.funcionario = User.objects.create_user(
            username="funcionario_listagem",
            email="funcionario_listagem@email.com",
            password="senha123",
        )
        grupo, _ = Group.objects.get_or_create(
            name="Funcionarios"
        )
        self.funcionario.groups.add(grupo)
        Leitor.objects.create(
            usuario=self.funcionario,
            nome_completo="Funcionário Teste",
            cpf="222.222.222-22",
            email="funcionario_listagem@email.com",
            telefone="(35) 99999-9999",
            endereco="Rua Teste, 2",
            tipo_vinculo="FUNCIONARIO",
            ativo=True,
        )
        Obra.objects.create(
            titulo="Obra Teste 1",
            autor="Autor Teste",
            isbn="1111111111111",
            editora="Editora Teste",
            ano_publicacao=2020,
            categoria="Teste",
            quantidade=1,
        )

    def test_listar_obras_requer_login(self):
        resposta = self.client.get(reverse("listar_obras"))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login/", resposta.url)

    def test_listar_obras_leitor_autenticado(self):
        self.client.force_login(self.leitor)
        resposta = self.client.get(reverse("listar_obras"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "biblioteca/obras/lista.html")
        self.assertIn("obras", resposta.context)

    def test_listar_obras_funcionario_autenticado(self):
        self.client.force_login(self.funcionario)
        resposta = self.client.get(reverse("listar_obras"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "biblioteca/obras/lista.html")

    def test_listar_leitores_requer_admin(self):
        self.client.force_login(self.leitor)
        resposta = self.client.get(reverse("listar_leitores"))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/", resposta.url)

    def test_listar_leitores_admin_autenticado(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse("listar_leitores"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "biblioteca/leitores/lista.html")
        self.assertIn("leitores", resposta.context)

    def test_gestao_dashboard_requer_admin(self):
        self.client.force_login(self.leitor)
        resposta = self.client.get(reverse("gestao_dashboard"))
        self.assertEqual(resposta.status_code, 302)

    def test_gestao_dashboard_admin_autenticado(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse("gestao_dashboard"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "biblioteca/gestao/dashboard.html")
        self.assertIn("total_contas", resposta.context)

    def test_gestao_usuarios_requer_admin(self):
        self.client.force_login(self.leitor)
        resposta = self.client.get(reverse("gestao_usuarios"))
        self.assertEqual(resposta.status_code, 302)

    def test_gestao_usuarios_admin_autenticado(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse("gestao_usuarios"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "biblioteca/gestao/usuarios.html")
        self.assertIn("contas", resposta.context)

    def test_gestao_solicitacoes_requer_admin(self):
        self.client.force_login(self.leitor)
        resposta = self.client.get(reverse("gestao_solicitacoes"))
        self.assertEqual(resposta.status_code, 302)

    def test_gestao_solicitacoes_admin_autenticado(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse("gestao_solicitacoes"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(
            resposta,
            "biblioteca/gestao/solicitacoes.html"
        )
        self.assertIn("pendentes", resposta.context)


class FormulariosCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username="admin_crud",
            email="admin_crud@email.com",
            password="senha123",
        )
        self.funcionario = User.objects.create_user(
            username="funcionario_crud",
            email="funcionario_crud@email.com",
            password="senha123",
        )
        grupo, _ = Group.objects.get_or_create(
            name="Funcionarios"
        )
        self.funcionario.groups.add(grupo)
        Leitor.objects.create(
            usuario=self.funcionario,
            nome_completo="Funcionário CRUD",
            cpf="333.333.333-33",
            email="funcionario_crud@email.com",
            telefone="(35) 99999-9999",
            endereco="Rua CRUD, 3",
            tipo_vinculo="FUNCIONARIO",
            ativo=True,
        )

    def test_cadastrar_obra_funcionario(self):
        self.client.force_login(self.funcionario)
        dados_obra = {
            "titulo": "Nova Obra Test",
            "autor": "Autor Test",
            "isbn": "9999999999999",
            "editora": "Editora Test",
            "ano_publicacao": 2025,
            "categoria": "Teste",
            "quantidade": 5,
        }
        resposta = self.client.post(
            reverse("cadastrar_obra"),
            dados_obra,
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(
            Obra.objects.filter(
                titulo="Nova Obra Test"
            ).exists()
        )
        obra = Obra.objects.get(titulo="Nova Obra Test")
        self.assertEqual(obra.autor, "Autor Test")
        self.assertEqual(obra.isbn, "9999999999999")
        self.assertEqual(obra.quantidade, 5)

    def test_editar_obra_funcionario(self):
        obra = Obra.objects.create(
            titulo="Obra para Editar",
            autor="Autor Original",
            isbn="1111111111111",
            editora="Editora Original",
            ano_publicacao=2020,
            categoria="Original",
            quantidade=2,
        )
        self.client.force_login(self.funcionario)
        dados_atualizados = {
            "titulo": "Obra Editada",
            "autor": "Autor Original",
            "isbn": obra.isbn,
            "editora": "Editora Original",
            "ano_publicacao": 2021,
            "categoria": "Editada",
            "quantidade": 8,
        }
        resposta = self.client.post(
            reverse("editar_obra", args=[obra.id]),
            dados_atualizados,
        )
        self.assertEqual(resposta.status_code, 302)
        obra.refresh_from_db()
        self.assertEqual(obra.titulo, "Obra Editada")
        self.assertEqual(obra.ano_publicacao, 2021)
        self.assertEqual(obra.quantidade, 8)

    def test_cadastrar_leitor_admin(self):
        self.client.force_login(self.admin)
        dados_leitor = {
            "nome_completo": "Novo Leitor",
            "cpf": "444.444.444-44",
            "email": "novo_leitor@email.com",
            "telefone": "(35) 88888-8888",
            "endereco": "Rua Novo, 44",
            "tipo_vinculo": "ALUNO",
            "ativo": "on",
        }
        resposta = self.client.post(
            reverse("cadastrar_leitor"),
            dados_leitor,
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(
            Leitor.objects.filter(
                email="novo_leitor@email.com"
            ).exists()
        )
        leitor = Leitor.objects.get(
            email="novo_leitor@email.com"
        )
        self.assertEqual(
            leitor.nome_completo,
            "Novo Leitor"
        )
        self.assertEqual(leitor.tipo_vinculo, "ALUNO")

    def test_editar_leitor_admin(self):
        leitor = Leitor.objects.create(
            nome_completo="Leitor para Editar",
            cpf="555.555.555-55",
            email="leitor_editar@email.com",
            telefone="(35) 77777-7777",
            endereco="Rua Editar, 55",
            tipo_vinculo="ALUNO",
            ativo=True,
        )
        self.client.force_login(self.admin)
        dados_atualizados = {
            "nome_completo": "Leitor Editado",
            "cpf": leitor.cpf,
            "email": leitor.email,
            "telefone": "(35) 66666-6666",
            "endereco": "Rua Nova, 66",
            "tipo_vinculo": "PROFESSOR",
            "ativo": "on",
        }
        resposta = self.client.post(
            reverse("editar_leitor", args=[leitor.id]),
            dados_atualizados,
        )
        self.assertEqual(resposta.status_code, 302)
        leitor.refresh_from_db()
        self.assertEqual(
            leitor.nome_completo,
            "Leitor Editado"
        )
        self.assertEqual(leitor.tipo_vinculo, "PROFESSOR")
        self.assertEqual(
            leitor.telefone,
            "(35) 66666-6666"
        )

    def test_cadastrar_obra_sem_permissao(self):
        leitor = User.objects.create_user(
            username="leitor_sem_perm",
            email="leitor_sem_perm@email.com",
            password="senha123",
        )
        self.client.force_login(leitor)
        dados_obra = {
            "titulo": "Obra Proibida",
            "autor": "Autor Proibido",
            "isbn": "0000000000000",
            "editora": "Editora Proibida",
            "ano_publicacao": 2025,
            "categoria": "Proibida",
            "quantidade": 1,
        }
        resposta = self.client.post(
            reverse("cadastrar_obra"),
            dados_obra,
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(
            Obra.objects.filter(
                titulo="Obra Proibida"
            ).exists()
        )

    def test_cadastrar_leitor_sem_permissao(self):
        leitor = User.objects.create_user(
            username="leitor_sem_perm2",
            email="leitor_sem_perm2@email.com",
            password="senha123",
        )
        self.client.force_login(leitor)
        dados_leitor = {
            "nome_completo": "Leitor Proibido",
            "cpf": "666.666.666-66",
            "email": "leitor_proibido@email.com",
            "telefone": "(35) 55555-5555",
            "endereco": "Rua Proibida, 66",
            "tipo_vinculo": "ALUNO",
            "ativo": "on",
        }
        resposta = self.client.post(
            reverse("cadastrar_leitor"),
            dados_leitor,
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(
            Leitor.objects.filter(
                email="leitor_proibido@email.com"
            ).exists()
        )


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
                id=self.obra.id, ativo=True
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