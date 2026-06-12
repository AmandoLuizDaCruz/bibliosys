from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    Emprestimo,
    Exemplar,
    Leitor,
    NotificacaoFuncionario,
    RegistroAuditoria,
    Reserva,
)


class ErroCirculacao(ValidationError):
    pass


def funcionario_aprovado(usuario):
    return (
        usuario.is_authenticated
        and not usuario.is_superuser
        and usuario.groups.filter(
            name="Funcionarios"
        ).exists()
    )


def obter_perfil_ativo(usuario):
    if not usuario.is_authenticated:
        raise ErroCirculacao(
            "É necessário entrar no sistema."
        )

    if usuario.is_superuser:
        raise ErroCirculacao(
            "O administrador não pode pegar ou reservar livros."
        )

    try:
        perfil = usuario.perfil_leitor
    except Leitor.DoesNotExist as erro:
        raise ErroCirculacao(
            "O usuário não possui um perfil de leitor."
        ) from erro

    if not perfil.ativo:
        raise ErroCirculacao(
            "Esta conta está inativa."
        )

    return perfil


def quantidade_emprestimos_ativos(usuario):
    return Emprestimo.objects.filter(
        usuario=usuario,
        status=Emprestimo.Status.ATIVO,
    ).count()


def validar_limite_emprestimos(usuario):
    perfil = obter_perfil_ativo(usuario)

    quantidade = quantidade_emprestimos_ativos(
        usuario
    )

    if quantidade >= perfil.limite_emprestimos:
        raise ErroCirculacao(
            (
                "O limite de empréstimos foi atingido. "
                f"Limite atual: {perfil.limite_emprestimos}."
            )
        )

    return perfil


def registrar_auditoria(
    usuario,
    acao,
    entidade,
    descricao,
    objeto_id="",
    endereco_ip=None,
):
    RegistroAuditoria.registrar(
        usuario=usuario,
        acao=acao,
        entidade=entidade,
        objeto_id=objeto_id,
        descricao=descricao,
        endereco_ip=endereco_ip,
    )


def criar_notificacao_reserva(reserva):
    if (
        reserva.status
        == Reserva.Status.AGUARDANDO_RETIRADA
    ):
        tipo = (
            NotificacaoFuncionario.Tipo.LIVRO_DISPONIVEL
        )

        titulo = "Livro aguardando retirada"

        mensagem = (
            f"{reserva.usuario.username} reservou "
            f'"{reserva.obra.titulo}". '
            f"O exemplar {reserva.exemplar.numero} "
            "está aguardando retirada."
        )

    else:
        tipo = (
            NotificacaoFuncionario.Tipo.NOVA_RESERVA
        )

        titulo = "Nova reserva na fila"

        mensagem = (
            f"{reserva.usuario.username} entrou na fila "
            f'de espera por "{reserva.obra.titulo}".'
        )

    return NotificacaoFuncionario.objects.create(
        reserva=reserva,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
    )


@transaction.atomic
def reservar_obra_leitor(
    usuario,
    obra,
    endereco_ip=None,
):
    validar_limite_emprestimos(usuario)

    if funcionario_aprovado(usuario):
        raise ErroCirculacao(
            (
                "Funcionários recebem livros disponíveis "
                "automaticamente."
            )
        )

    reserva_existente = Reserva.objects.filter(
        usuario=usuario,
        obra=obra,
        status__in=[
            Reserva.Status.FILA,
            Reserva.Status.AGUARDANDO_RETIRADA,
        ],
    ).exists()

    if reserva_existente:
        raise ErroCirculacao(
            "Você já possui uma reserva ativa para este livro."
        )

    exemplar = (
        Exemplar.objects
        .select_for_update()
        .filter(
            obra=obra,
            numero__gt=1,
            status=Exemplar.Status.DISPONIVEL,
            somente_consulta=False,
        )
        .order_by("numero")
        .first()
    )

    reserva = Reserva.objects.create(
        usuario=usuario,
        obra=obra,
        status=Reserva.Status.FILA,
    )

    if exemplar:
        reserva.disponibilizar_para_retirada(
            exemplar
        )

    criar_notificacao_reserva(reserva)

    registrar_auditoria(
        usuario=usuario,
        acao=RegistroAuditoria.Acao.RESERVA,
        entidade="Reserva",
        objeto_id=reserva.id,
        descricao=(
            f'Reservou o livro "{obra.titulo}". '
            f"Situação: {reserva.get_status_display()}."
        ),
        endereco_ip=endereco_ip,
    )

    return reserva


@transaction.atomic
def emprestar_automaticamente_funcionario(
    usuario,
    obra,
    endereco_ip=None,
):
    if not funcionario_aprovado(usuario):
        raise ErroCirculacao(
            "Somente funcionários aprovados usam empréstimo automático."
        )

    validar_limite_emprestimos(usuario)

    exemplar = (
        Exemplar.objects
        .select_for_update()
        .filter(
            obra=obra,
            numero__gt=1,
            status=Exemplar.Status.DISPONIVEL,
            somente_consulta=False,
        )
        .order_by("numero")
        .first()
    )

    if exemplar is None:
        raise ErroCirculacao(
            "Não existe exemplar disponível para empréstimo."
        )

    exemplar.status = Exemplar.Status.EMPRESTADO

    exemplar.save(
        update_fields=[
            "status",
            "somente_consulta",
            "atualizado_em",
        ]
    )

    emprestimo = Emprestimo.objects.create(
        usuario=usuario,
        exemplar=exemplar,
        registrado_por=usuario,
    )

    registrar_auditoria(
        usuario=usuario,
        acao=RegistroAuditoria.Acao.EMPRESTIMO,
        entidade="Emprestimo",
        objeto_id=emprestimo.id,
        descricao=(
            f'Pegou automaticamente o livro '
            f'"{obra.titulo}", exemplar {exemplar.numero}.'
        ),
        endereco_ip=endereco_ip,
    )

    return emprestimo


def solicitar_obra(
    usuario,
    obra,
    endereco_ip=None,
):
    if usuario.is_superuser:
        raise ErroCirculacao(
            "O administrador não pode pegar ou reservar livros."
        )

    if funcionario_aprovado(usuario):
        return emprestar_automaticamente_funcionario(
            usuario=usuario,
            obra=obra,
            endereco_ip=endereco_ip,
        )

    return reservar_obra_leitor(
        usuario=usuario,
        obra=obra,
        endereco_ip=endereco_ip,
    )


@transaction.atomic
def registrar_retirada_reserva(
    funcionario,
    reserva,
    endereco_ip=None,
):
    if not funcionario_aprovado(funcionario):
        raise ErroCirculacao(
            "Somente funcionários podem registrar retiradas."
        )

    reserva = (
        Reserva.objects
        .select_for_update()
        .select_related(
            "usuario",
            "obra",
            "exemplar",
        )
        .get(pk=reserva.pk)
    )

    if (
        reserva.status
        != Reserva.Status.AGUARDANDO_RETIRADA
    ):
        raise ErroCirculacao(
            "Esta reserva não está aguardando retirada."
        )

    if reserva.esta_expirada:
        raise ErroCirculacao(
            "Esta reserva expirou."
        )

    if reserva.exemplar is None:
        raise ErroCirculacao(
            "A reserva não possui exemplar associado."
        )

    validar_limite_emprestimos(
        reserva.usuario
    )

    exemplar = (
        Exemplar.objects
        .select_for_update()
        .get(pk=reserva.exemplar.pk)
    )

    if exemplar.status != Exemplar.Status.RESERVADO:
        raise ErroCirculacao(
            "O exemplar não está mais reservado."
        )

    exemplar.status = Exemplar.Status.EMPRESTADO

    exemplar.save(
        update_fields=[
            "status",
            "somente_consulta",
            "atualizado_em",
        ]
    )

    agora = timezone.now()

    reserva.status = Reserva.Status.RETIRADA
    reserva.finalizada_em = agora

    reserva.save(
        update_fields=[
            "status",
            "finalizada_em",
        ]
    )

    reserva.notificacoes_funcionarios.update(
        ativa=False
    )

    emprestimo = Emprestimo.objects.create(
        usuario=reserva.usuario,
        exemplar=exemplar,
        reserva=reserva,
        registrado_por=funcionario,
    )

    registrar_auditoria(
        usuario=funcionario,
        acao=RegistroAuditoria.Acao.EMPRESTIMO,
        entidade="Emprestimo",
        objeto_id=emprestimo.id,
        descricao=(
            f"Registrou a retirada de "
            f'"{reserva.obra.titulo}" para '
            f"{reserva.usuario.username}."
        ),
        endereco_ip=endereco_ip,
    )

    return emprestimo


def promover_proximo_da_fila(
    obra,
    exemplar,
):
    proxima_reserva = (
        Reserva.objects
        .select_for_update()
        .filter(
            obra=obra,
            status=Reserva.Status.FILA,
        )
        .order_by("criada_em")
        .first()
    )

    if proxima_reserva is None:
        return None

    proxima_reserva.disponibilizar_para_retirada(
        exemplar
    )

    criar_notificacao_reserva(
        proxima_reserva
    )

    return proxima_reserva


@transaction.atomic
def expirar_reserva(
    reserva,
):
    reserva = (
        Reserva.objects
        .select_for_update()
        .select_related(
            "obra",
            "exemplar",
        )
        .get(pk=reserva.pk)
    )

    if (
        reserva.status
        != Reserva.Status.AGUARDANDO_RETIRADA
    ):
        return False

    if not reserva.esta_expirada:
        return False

    exemplar = reserva.exemplar
    agora = timezone.now()

    reserva.status = Reserva.Status.EXPIRADA
    reserva.finalizada_em = agora

    reserva.save(
        update_fields=[
            "status",
            "finalizada_em",
        ]
    )

    reserva.notificacoes_funcionarios.update(
        ativa=False
    )

    if exemplar:
        exemplar = (
            Exemplar.objects
            .select_for_update()
            .get(pk=exemplar.pk)
        )

        exemplar.status = Exemplar.Status.DISPONIVEL

        exemplar.save(
            update_fields=[
                "status",
                "somente_consulta",
                "atualizado_em",
            ]
        )

        promover_proximo_da_fila(
            reserva.obra,
            exemplar,
        )

    registrar_auditoria(
        usuario=None,
        acao=RegistroAuditoria.Acao.ALTERACAO,
        entidade="Reserva",
        objeto_id=reserva.id,
        descricao=(
            f'A reserva de "{reserva.obra.titulo}" '
            "expirou após 24 horas."
        ),
    )

    return True


def expirar_reservas_vencidas():
    agora = timezone.now()

    identificadores = list(
        Reserva.objects.filter(
            status=Reserva.Status.AGUARDANDO_RETIRADA,
            expira_em__lte=agora,
        ).values_list(
            "id",
            flat=True,
        )
    )

    quantidade = 0

    for reserva_id in identificadores:
        reserva = Reserva.objects.get(
            id=reserva_id
        )

        if expirar_reserva(reserva):
            quantidade += 1

    return quantidade
