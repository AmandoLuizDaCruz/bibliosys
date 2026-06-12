from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .models import Leitor, RegistroAuditoria


User = get_user_model()


class EdicaoProprioPerfilTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario_teste",
            email="usuario@teste.com",
            password="123",
            first_name="Usuário",
            last_name="Teste",
        )

        self.perfil = Leitor.objects.create(
            usuario=self.usuario,
            nome_completo="Usuário Teste",
            cpf="111.222.333-44",
            email="usuario@teste.com",
            telefone="(35) 99999-1111",
            endereco="Rua Antiga, 10",
            tipo_vinculo="ALUNO",
            ativo=True,
        )

        self.admin = User.objects.create_superuser(
            username="Admin",
            email="admin@teste.com",
            password="Admin",
        )

    def dados_validos(self):
        return {
            "username": "usuario_atualizado",
            "first_name": "Nome",
            "last_name": "Atualizado",
            "email": "atualizado@teste.com",
            "cpf": "99988877766",
            "telefone": "35988887777",
            "endereco": "Rua Nova, 200",
            "nova_senha": "",
            "confirmar_senha": "",
        }

    def test_usuario_nao_autenticado_e_redirecionado(self):
        resposta = self.client.get(
            reverse("editar_meu_perfil")
        )

        self.assertEqual(
            resposta.status_code,
            302,
        )

    def test_usuario_edita_os_proprios_dados(self):
        self.client.force_login(
            self.usuario
        )

        resposta = self.client.post(
            reverse("editar_meu_perfil"),
            self.dados_validos(),
        )

        self.usuario.refresh_from_db()
        self.perfil.refresh_from_db()

        self.assertEqual(
            resposta.status_code,
            302,
        )

        self.assertEqual(
            self.usuario.username,
            "usuario_atualizado",
        )

        self.assertEqual(
            self.usuario.email,
            "atualizado@teste.com",
        )

        self.assertEqual(
            self.perfil.nome_completo,
            "Nome Atualizado",
        )

        self.assertEqual(
            self.perfil.cpf,
            "999.888.777-66",
        )

        self.assertEqual(
            self.perfil.telefone,
            "(35) 98888-7777",
        )

        self.assertTrue(
            RegistroAuditoria.objects.filter(
                usuario=self.usuario,
                entidade="Próprio perfil",
            ).exists()
        )

    def test_usuario_nao_altera_permissoes_ou_cargo(self):
        grupo, _ = Group.objects.get_or_create(
            name="Funcionarios"
        )

        self.usuario.groups.add(grupo)
        self.perfil.tipo_vinculo = "FUNCIONARIO"
        self.perfil.save(
            update_fields=["tipo_vinculo"]
        )

        self.client.force_login(
            self.usuario
        )

        dados = self.dados_validos()

        dados.update(
            {
                "is_superuser": "on",
                "is_staff": "on",
                "is_active": "",
                "nivel_acesso": "ADMIN",
                "tipo_vinculo": "EXTERNO",
            }
        )

        self.client.post(
            reverse("editar_meu_perfil"),
            dados,
        )

        self.usuario.refresh_from_db()
        self.perfil.refresh_from_db()

        self.assertFalse(
            self.usuario.is_superuser
        )

        self.assertFalse(
            self.usuario.is_staff
        )

        self.assertTrue(
            self.usuario.is_active
        )

        self.assertTrue(
            self.usuario.groups.filter(
                name="Funcionarios"
            ).exists()
        )

        self.assertEqual(
            self.perfil.tipo_vinculo,
            "FUNCIONARIO",
        )

    def test_usuario_altera_senha_e_continua_logado(self):
        self.client.force_login(
            self.usuario
        )

        dados = self.dados_validos()

        dados["nova_senha"] = "nova123"
        dados["confirmar_senha"] = "nova123"

        resposta = self.client.post(
            reverse("editar_meu_perfil"),
            dados,
        )

        self.usuario.refresh_from_db()

        self.assertEqual(
            resposta.status_code,
            302,
        )

        self.assertTrue(
            self.usuario.check_password(
                "nova123"
            )
        )

        resposta_seguinte = self.client.get(
            reverse("editar_meu_perfil")
        )

        self.assertEqual(
            resposta_seguinte.status_code,
            200,
        )

    def test_admin_nao_edita_pela_tela(self):
        self.client.force_login(
            self.admin
        )

        resposta = self.client.get(
            reverse("editar_meu_perfil")
        )

        self.assertEqual(
            resposta.status_code,
            302,
        )

