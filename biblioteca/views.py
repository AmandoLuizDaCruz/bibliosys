from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CadastroUsuarioForm, LeitorForm, ObraForm
from .models import Leitor, Obra, SolicitacaoFuncionario


User = get_user_model()


def administrador_required(view_function):
    @wraps(view_function)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_superuser:
            messages.error(
                request,
                "Esta área é exclusiva do administrador.",
            )
            return redirect("home")

        return view_function(request, *args, **kwargs)

    return wrapper


def pode_gerenciar_obras(usuario):
    """
    Somente funcionários aprovados podem gerenciar livros.

    O administrador não participa da gestão do acervo.
    """
    if not usuario.is_authenticated:
        return False

    if usuario.is_superuser:
        return False

    return usuario.groups.filter(
        name="Funcionarios"
    ).exists()


def home(request):
    solicitacao = None

    if request.user.is_authenticated:
        try:
            solicitacao = (
                request.user.solicitacao_funcionario
            )
        except SolicitacaoFuncionario.DoesNotExist:
            pass

    return render(
        request,
        "biblioteca/home.html",
        {
            "solicitacao": solicitacao,
            "pode_gerenciar_obras": pode_gerenciar_obras(
                request.user
            ),
        },
    )


def entrar(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("gestao_dashboard")

        return redirect("home")

    formulario = AuthenticationForm(
        request,
        data=request.POST or None,
    )

    if request.method == "POST" and formulario.is_valid():
        usuario = formulario.get_user()

        login(request, usuario)

        if usuario.is_superuser:
            return redirect("gestao_dashboard")

        return redirect("home")

    return render(
        request,
        "biblioteca/autenticacao/login.html",
        {
            "formulario": formulario,
        },
    )


def cadastrar_usuario(request):
    if request.user.is_authenticated:
        return redirect("home")

    formulario = CadastroUsuarioForm(
        request.POST or None
    )

    if request.method == "POST" and formulario.is_valid():
        usuario = formulario.save()

        login(request, usuario)

        try:
            usuario.solicitacao_funcionario
        except SolicitacaoFuncionario.DoesNotExist:
            messages.success(
                request,
                "Conta de leitor criada com sucesso.",
            )
        else:
            messages.info(
                request,
                (
                    "Conta criada. Sua solicitação para funcionário "
                    "está aguardando aprovação."
                ),
            )

        return redirect("home")

    return render(
        request,
        "biblioteca/autenticacao/cadastro.html",
        {
            "formulario": formulario,
        },
    )


@login_required(login_url="login")
def sair(request):
    logout(request)
    return redirect("login")


# =========================================================
# LIVROS
# =========================================================

@login_required(login_url="login")
def listar_obras(request):
    obras = Obra.objects.all().order_by("titulo")

    return render(
        request,
        "biblioteca/obras/lista.html",
        {
            "obras": obras,
            "pode_gerenciar_obras": pode_gerenciar_obras(
                request.user
            ),
        },
    )


@login_required(login_url="login")
def cadastrar_obra(request):
    if not pode_gerenciar_obras(request.user):
        messages.error(
            request,
            (
                "Somente funcionários aprovados podem "
                "cadastrar livros."
            ),
        )

        if request.user.is_superuser:
            return redirect("gestao_dashboard")

        return redirect("listar_obras")

    formulario = ObraForm(request.POST or None)

    if request.method == "POST" and formulario.is_valid():
        formulario.save()

        messages.success(
            request,
            "Livro cadastrado com sucesso.",
        )

        return redirect("listar_obras")

    return render(
        request,
        "biblioteca/obras/formulario.html",
        {
            "formulario": formulario,
            "titulo": "Cadastrar livro",
        },
    )


@login_required(login_url="login")
def editar_obra(request, obra_id):
    if not pode_gerenciar_obras(request.user):
        messages.error(
            request,
            (
                "Somente funcionários aprovados podem "
                "editar livros."
            ),
        )

        if request.user.is_superuser:
            return redirect("gestao_dashboard")

        return redirect("listar_obras")

    obra = get_object_or_404(
        Obra,
        id=obra_id,
    )

    formulario = ObraForm(
        request.POST or None,
        instance=obra,
    )

    if request.method == "POST" and formulario.is_valid():
        formulario.save()

        messages.success(
            request,
            "Livro atualizado com sucesso.",
        )

        return redirect("listar_obras")

    return render(
        request,
        "biblioteca/obras/formulario.html",
        {
            "formulario": formulario,
            "titulo": "Editar livro",
        },
    )


@login_required(login_url="login")
def excluir_obra(request, obra_id):
    if not pode_gerenciar_obras(request.user):
        messages.error(
            request,
            (
                "Somente funcionários aprovados podem "
                "excluir livros."
            ),
        )

        if request.user.is_superuser:
            return redirect("gestao_dashboard")

        return redirect("listar_obras")

    obra = get_object_or_404(
        Obra,
        id=obra_id,
    )

    if request.method == "POST":
        obra.delete()

        messages.success(
            request,
            "Livro excluído com sucesso.",
        )

        return redirect("listar_obras")

    return render(
        request,
        "biblioteca/obras/excluir.html",
        {
            "obra": obra,
        },
    )


# =========================================================
# LEITORES
# =========================================================

@login_required(login_url="login")
def listar_leitores(request):
    if not request.user.is_superuser:
        messages.error(
            request,
            "Somente o administrador pode acessar os usuários.",
        )
        return redirect("home")

    leitores = Leitor.objects.all().order_by(
        "nome_completo"
    )

    return render(
        request,
        "biblioteca/leitores/lista.html",
        {
            "leitores": leitores,
        },
    )


@login_required(login_url="login")
def cadastrar_leitor(request):
    if not request.user.is_superuser:
        messages.error(
            request,
            "Somente o administrador pode cadastrar leitores.",
        )
        return redirect("home")

    formulario = LeitorForm(
        request.POST or None
    )

    if request.method == "POST" and formulario.is_valid():
        formulario.save()

        messages.success(
            request,
            "Leitor cadastrado com sucesso.",
        )

        return redirect("listar_leitores")

    return render(
        request,
        "biblioteca/leitores/formulario.html",
        {
            "formulario": formulario,
            "titulo": "Cadastrar leitor",
        },
    )


@login_required(login_url="login")
def editar_leitor(request, leitor_id):
    if not request.user.is_superuser:
        messages.error(
            request,
            "Somente o administrador pode editar leitores.",
        )
        return redirect("home")

    leitor = get_object_or_404(
        Leitor,
        id=leitor_id,
    )

    formulario = LeitorForm(
        request.POST or None,
        instance=leitor,
    )

    if request.method == "POST" and formulario.is_valid():
        formulario.save()

        messages.success(
            request,
            "Leitor atualizado com sucesso.",
        )

        return redirect("listar_leitores")

    return render(
        request,
        "biblioteca/leitores/formulario.html",
        {
            "formulario": formulario,
            "titulo": "Editar leitor",
        },
    )


@login_required(login_url="login")
def excluir_leitor(request, leitor_id):
    if not request.user.is_superuser:
        messages.error(
            request,
            "Somente o administrador pode excluir leitores.",
        )
        return redirect("home")

    leitor = get_object_or_404(
        Leitor,
        id=leitor_id,
    )

    if request.method == "POST":
        if leitor.usuario:
            if (
                leitor.usuario.username.casefold()
                == "admin"
            ):
                messages.error(
                    request,
                    "A conta Admin não pode ser excluída.",
                )
                return redirect("listar_leitores")

            leitor.usuario.delete()
        else:
            leitor.delete()

        messages.success(
            request,
            "Leitor excluído com sucesso.",
        )

        return redirect("listar_leitores")

    return render(
        request,
        "biblioteca/leitores/excluir.html",
        {
            "leitor": leitor,
        },
    )


# =========================================================
# ÁREA DE GESTÃO
# =========================================================

@administrador_required
def gestao_dashboard(request):
    solicitacoes_pendentes = (
        SolicitacaoFuncionario.objects
        .filter(
            status=(
                SolicitacaoFuncionario
                .Status
                .PENDENTE
            )
        )
        .select_related("usuario")
        .order_by("-criada_em")
    )

    contexto = {
        "total_contas": User.objects.count(),
        "total_leitores": Leitor.objects.count(),
        "total_pendentes": (
            solicitacoes_pendentes.count()
        ),
        "solicitacoes_recentes": (
            solicitacoes_pendentes[:5]
        ),
    }

    return render(
        request,
        "biblioteca/gestao/dashboard.html",
        contexto,
    )


@administrador_required
def gestao_usuarios(request):
    consulta = request.GET.get(
        "q",
        "",
    ).strip()

    usuarios = User.objects.all().order_by(
        "username"
    )

    if consulta:
        usuarios = usuarios.filter(
            Q(username__icontains=consulta)
            | Q(first_name__icontains=consulta)
            | Q(last_name__icontains=consulta)
            | Q(email__icontains=consulta)
            | Q(
                perfil_leitor__nome_completo__icontains=(
                    consulta
                )
            )
            | Q(
                perfil_leitor__cpf__icontains=consulta
            )
        ).distinct()

    contas = []

    for usuario in usuarios:
        try:
            perfil = usuario.perfil_leitor
        except Leitor.DoesNotExist:
            perfil = None

        try:
            solicitacao = (
                usuario.solicitacao_funcionario
            )
        except SolicitacaoFuncionario.DoesNotExist:
            solicitacao = None

        if usuario.username.casefold() == "admin":
            nivel = "Administrador master"
            classe_nivel = "administrador"

        elif usuario.groups.filter(
            name="Funcionarios"
        ).exists():
            nivel = "Funcionário"
            classe_nivel = "funcionario"

        elif (
            solicitacao
            and solicitacao.status
            == SolicitacaoFuncionario.Status.PENDENTE
        ):
            nivel = "Aprovação pendente"
            classe_nivel = "pendente"

        elif (
            solicitacao
            and solicitacao.status
            == SolicitacaoFuncionario.Status.RECUSADA
        ):
            nivel = "Leitor — solicitação recusada"
            classe_nivel = "recusada"

        else:
            nivel = "Leitor"
            classe_nivel = "leitor"

        contas.append(
            {
                "usuario": usuario,
                "perfil": perfil,
                "solicitacao": solicitacao,
                "nivel": nivel,
                "classe_nivel": classe_nivel,
            }
        )

    return render(
        request,
        "biblioteca/gestao/usuarios.html",
        {
            "contas": contas,
            "consulta": consulta,
        },
    )


@administrador_required
def gestao_excluir_usuario(request, usuario_id):
    usuario = get_object_or_404(
        User,
        id=usuario_id,
    )

    if usuario.username.casefold() == "admin":
        messages.error(
            request,
            (
                "A conta Admin é protegida e "
                "não pode ser excluída."
            ),
        )
        return redirect("gestao_usuarios")

    try:
        perfil = usuario.perfil_leitor
    except Leitor.DoesNotExist:
        perfil = None

    if request.method == "POST":
        nome_usuario = usuario.username

        filtros = Q(usuario=usuario)

        if usuario.email:
            filtros |= Q(
                email__iexact=usuario.email.strip()
            )

        if perfil:
            if perfil.email:
                filtros |= Q(
                    email__iexact=perfil.email.strip()
                )

            if perfil.cpf:
                filtros |= Q(
                    cpf=perfil.cpf
                )

        Leitor.objects.filter(
            filtros
        ).delete()

        usuario.delete()

        messages.success(
            request,
            (
                f'A conta "{nome_usuario}" '
                "foi excluída completamente."
            ),
        )

        return redirect("gestao_usuarios")

    return render(
        request,
        "biblioteca/gestao/confirmar_exclusao.html",
        {
            "conta": usuario,
            "perfil": perfil,
        },
    )


@administrador_required
def gestao_solicitacoes(request):
    pendentes = (
        SolicitacaoFuncionario.objects
        .filter(
            status=(
                SolicitacaoFuncionario
                .Status
                .PENDENTE
            )
        )
        .select_related(
            "usuario",
            "usuario__perfil_leitor",
        )
        .order_by("-criada_em")
    )

    historico = (
        SolicitacaoFuncionario.objects
        .exclude(
            status=(
                SolicitacaoFuncionario
                .Status
                .PENDENTE
            )
        )
        .select_related(
            "usuario",
            "analisada_por",
        )
        .order_by("-analisada_em")
    )

    return render(
        request,
        "biblioteca/gestao/solicitacoes.html",
        {
            "pendentes": pendentes,
            "historico": historico,
        },
    )


@administrador_required
def gestao_aprovar_solicitacao(
    request,
    solicitacao_id,
):
    if request.method != "POST":
        return redirect("gestao_solicitacoes")

    solicitacao = get_object_or_404(
        SolicitacaoFuncionario,
        id=solicitacao_id,
    )

    if (
        solicitacao.status
        != SolicitacaoFuncionario.Status.PENDENTE
    ):
        messages.warning(
            request,
            "Essa solicitação já foi analisada.",
        )
        return redirect("gestao_solicitacoes")

    solicitacao.aprovar(request.user)

    messages.success(
        request,
        (
            f"O funcionário "
            f"{solicitacao.usuario.username} "
            "foi aprovado."
        ),
    )

    return redirect("gestao_solicitacoes")


@administrador_required
def gestao_recusar_solicitacao(
    request,
    solicitacao_id,
):
    if request.method != "POST":
        return redirect("gestao_solicitacoes")

    solicitacao = get_object_or_404(
        SolicitacaoFuncionario,
        id=solicitacao_id,
    )

    if (
        solicitacao.status
        != SolicitacaoFuncionario.Status.PENDENTE
    ):
        messages.warning(
            request,
            "Essa solicitação já foi analisada.",
        )
        return redirect("gestao_solicitacoes")

    solicitacao.recusar(request.user)

    messages.success(
        request,
        (
            f"A solicitação de "
            f"{solicitacao.usuario.username} "
            "foi recusada."
        ),
    )

    return redirect("gestao_solicitacoes")