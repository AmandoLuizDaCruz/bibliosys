from django.contrib import messages
from django.contrib.auth import (
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms_perfil import EdicaoProprioPerfilForm
from .models import Leitor, RegistroAuditoria


def obter_endereco_ip(request):
    encaminhado = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if encaminhado:
        return encaminhado.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def dados_pessoais_usuario(usuario):
    try:
        perfil = usuario.perfil_leitor
    except Leitor.DoesNotExist:
        perfil = None

    return {
        "username": usuario.username,
        "first_name": usuario.first_name,
        "last_name": usuario.last_name,
        "email": usuario.email,
        "cpf": (
            perfil.cpf
            if perfil
            else None
        ),
        "telefone": (
            perfil.telefone
            if perfil
            else None
        ),
        "endereco": (
            perfil.endereco
            if perfil
            else None
        ),
    }


@login_required(login_url="login")
def editar_meu_perfil(request):
    if request.user.is_superuser:
        messages.info(
            request,
            (
                "A conta Admin é protegida e somente "
                "pode ser alterada pelo código."
            ),
        )

        return redirect("gestao_dashboard")

    dados_anteriores = dados_pessoais_usuario(
        request.user
    )

    formulario = EdicaoProprioPerfilForm(
        request.POST or None,
        usuario=request.user,
    )

    if request.method == "POST" and formulario.is_valid():
        usuario, senha_alterada = formulario.save()

        if senha_alterada:
            update_session_auth_hash(
                request,
                usuario,
            )

        dados_novos = dados_pessoais_usuario(
            usuario
        )

        RegistroAuditoria.registrar(
            usuario=usuario,
            acao=RegistroAuditoria.Acao.ALTERACAO,
            entidade="Próprio perfil",
            objeto_id=usuario.id,
            descricao=(
                f'O usuário "{usuario.username}" '
                "alterou os próprios dados pessoais."
            ),
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            endereco_ip=obter_endereco_ip(request),
        )

        messages.success(
            request,
            "Seus dados foram atualizados com sucesso.",
        )

        return redirect("editar_meu_perfil")

    try:
        perfil = request.user.perfil_leitor
    except Leitor.DoesNotExist:
        perfil = None

    funcionario = request.user.groups.filter(
        name="Funcionarios"
    ).exists()

    contexto = {
        "formulario": formulario,
        "perfil": perfil,
        "tipo_conta": (
            "Funcionário"
            if funcionario
            else "Leitor"
        ),
    }

    return render(
        request,
        "biblioteca/perfil/editar.html",
        contexto,
    )
