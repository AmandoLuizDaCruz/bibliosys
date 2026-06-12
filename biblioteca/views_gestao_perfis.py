from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms_gestao import EdicaoCompletaUsuarioForm
from .models import Leitor, RegistroAuditoria
from .views import administrador_required


User = get_user_model()


def obter_endereco_ip(request):
    encaminhado = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if encaminhado:
        return encaminhado.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def dados_usuario(usuario):
    try:
        perfil = usuario.perfil_leitor
    except Leitor.DoesNotExist:
        perfil = None

    return {
        "username": usuario.username,
        "nome": usuario.first_name,
        "sobrenome": usuario.last_name,
        "email": usuario.email,
        "ativo": usuario.is_active,
        "cpf": perfil.cpf if perfil else None,
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
        "tipo_vinculo": (
            perfil.tipo_vinculo
            if perfil
            else None
        ),
        "nivel_acesso": (
            "FUNCIONARIO"
            if usuario.groups.filter(
                name="Funcionarios"
            ).exists()
            else "LEITOR"
        ),
    }


@administrador_required
def gestao_editar_usuario(
    request,
    usuario_id,
):
    usuario = get_object_or_404(
        User,
        id=usuario_id,
    )

    if usuario.username.casefold() == "admin":
        messages.error(
            request,
            (
                "A conta Admin é protegida. "
                "Ela somente pode ser alterada pelo código."
            ),
        )

        return redirect("gestao_usuarios")

    dados_anteriores = dados_usuario(usuario)

    formulario = EdicaoCompletaUsuarioForm(
        request.POST or None,
        usuario=usuario,
        administrador=request.user,
    )

    if request.method == "POST" and formulario.is_valid():
        usuario = formulario.save()

        dados_novos = dados_usuario(usuario)

        RegistroAuditoria.registrar(
            usuario=request.user,
            acao=RegistroAuditoria.Acao.ALTERACAO,
            entidade="Perfil de usuário",
            objeto_id=usuario.id,
            descricao=(
                f'O administrador alterou completamente '
                f'o perfil de "{usuario.username}".'
            ),
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            endereco_ip=obter_endereco_ip(request),
        )

        messages.success(
            request,
            (
                f'O perfil de "{usuario.username}" '
                "foi atualizado com sucesso."
            ),
        )

        return redirect("gestao_usuarios")

    return render(
        request,
        "biblioteca/gestao/editar_usuario.html",
        {
            "formulario": formulario,
            "conta": usuario,
        },
    )
