from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    ConfiguracaoBiblioteca,
    Emprestimo,
    Exemplar,
    Leitor,
    Multa,
    NotificacaoFuncionario,
    RegistroAuditoria,
    Renovacao,
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
            "O administrador não participa da circulação de livros."
        )

    try:
        perfil = usuario.perfil_leitor
    except Leitor.DoesNotExist as erro:
        raise ErroCirculacao(
            "O usuário não possui perfil de leitor."
        ) from erro

    if not perfil.ativo or not usuario.is_active:
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
    dados_anteriores=None,
    dados_novos=None,
):
    return RegistroAuditoria.registrar(
        usuario=usuario,
        acao=acao,
        entidade=entidade,
        objeto_id=objeto_id,
        descricao=descricao,
        endereco_ip=endereco_ip,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
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
            "está separado para retirada."
        )

    else:
        tipo = NotificacaoFuncionario.Tipo.NOVA_RESERVA
        titulo = "Nova entrada na fila"

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
            "Você já possui um pedido ativo para este livro."
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

    # O livro sai do estoque imediatamente quando existe
    # exemplar disponível.
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
            f'Pediu o livro "{obra.titulo}". '
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
            "Somente funcionários aprovados recebem livros automaticamente."
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
        entidade="Empréstimo",
        objeto_id=emprestimo.id,
        descricao=(
            f'Pegou automaticamente "{obra.titulo}", '
            f"exemplar {exemplar.numero}."
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
            "Este pedido não está aguardando retirada."
        )

    if reserva.esta_expirada:
        raise ErroCirculacao(
            "O prazo para retirada deste pedido expirou."
        )

    if reserva.exemplar is None:
        raise ErroCirculacao(
            "O pedido não possui exemplar associado."
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

    reserva.status = Reserva.Status.RETIRADA
    reserva.finalizada_em = timezone.now()

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
        entidade="Empréstimo",
        objeto_id=emprestimo.id,
        descricao=(
            f'Registrou a retirada de "{reserva.obra.titulo}" '
            f"para {reserva.usuario.username}."
        ),
        endereco_ip=endereco_ip,
    )

    return emprestimo


@transaction.atomic
def renovar_emprestimo(
    usuario,
    emprestimo,
    endereco_ip=None,
):
    obter_perfil_ativo(usuario)

    emprestimo = (
        Emprestimo.objects
        .select_for_update()
        .select_related(
            "usuario",
            "exemplar",
            "exemplar__obra",
        )
        .get(pk=emprestimo.pk)
    )

    if emprestimo.usuario_id != usuario.id:
        raise ErroCirculacao(
            "Você não pode renovar o empréstimo de outra pessoa."
        )

    if emprestimo.status != Emprestimo.Status.ATIVO:
        raise ErroCirculacao(
            "Este empréstimo não está ativo."
        )

    if emprestimo.esta_atrasado:
        raise ErroCirculacao(
            "Um empréstimo atrasado não pode ser renovado."
        )

    if emprestimo.quantidade_renovacoes >= 1:
        raise ErroCirculacao(
            "Este empréstimo já foi renovado."
        )

    existe_fila = Reserva.objects.filter(
        obra=emprestimo.exemplar.obra,
        status__in=[
            Reserva.Status.FILA,
            Reserva.Status.AGUARDANDO_RETIRADA,
        ],
    ).exclude(
        usuario=usuario
    ).exists()

    if existe_fila:
        raise ErroCirculacao(
            (
                "A renovação não pode ser realizada porque "
                "existem pessoas aguardando este livro."
            )
        )

    configuracao = ConfiguracaoBiblioteca.carregar()

    data_anterior = (
        emprestimo.data_prevista_devolucao
    )

    nova_data = (
        data_anterior
        + timedelta(
            days=configuracao.prazo_renovacao_dias
        )
    )

    emprestimo.data_prevista_devolucao = nova_data
    emprestimo.quantidade_renovacoes += 1

    emprestimo.save(
        update_fields=[
            "data_prevista_devolucao",
            "quantidade_renovacoes",
        ]
    )

    Renovacao.objects.create(
        emprestimo=emprestimo,
        solicitada_por=usuario,
        data_anterior=data_anterior,
        nova_data=nova_data,
    )

    registrar_auditoria(
        usuario=usuario,
        acao=RegistroAuditoria.Acao.RENOVACAO,
        entidade="Empréstimo",
        objeto_id=emprestimo.id,
        descricao=(
            f'Renovou "{emprestimo.exemplar.obra.titulo}" '
            f"até {nova_data:%d/%m/%Y}."
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
        .order_by(
            "criada_em",
            "id",
        )
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
def registrar_devolucao(
    funcionario,
    emprestimo,
    endereco_ip=None,
):
    if not funcionario_aprovado(funcionario):
        raise ErroCirculacao(
            "Somente funcionários podem dar baixa em livros."
        )

    emprestimo = (
        Emprestimo.objects
        .select_for_update()
        .select_related(
            "usuario",
            "exemplar",
            "exemplar__obra",
        )
        .get(pk=emprestimo.pk)
    )

    if emprestimo.status != Emprestimo.Status.ATIVO:
        raise ErroCirculacao(
            "Este empréstimo já foi finalizado."
        )

    exemplar = (
        Exemplar.objects
        .select_for_update()
        .get(pk=emprestimo.exemplar.pk)
    )

    emprestimo.status = Emprestimo.Status.DEVOLVIDO
    emprestimo.data_devolucao = timezone.now()

    emprestimo.save(
        update_fields=[
            "status",
            "data_devolucao",
        ]
    )

    multa = None

    if emprestimo.dias_atraso > 0:
        multa, _ = Multa.objects.get_or_create(
            emprestimo=emprestimo,
            defaults={
                "registrada_por": funcionario,
            },
        )

        multa.registrada_por = funcionario
        multa.recalcular()

        multa.save(
            update_fields=[
                "registrada_por",
            ]
        )

    exemplar.status = Exemplar.Status.DISPONIVEL

    exemplar.save(
        update_fields=[
            "status",
            "somente_consulta",
            "atualizado_em",
        ]
    )

    promovida = promover_proximo_da_fila(
        obra=exemplar.obra,
        exemplar=exemplar,
    )

    descricao = (
        f'Registrou a devolução de '
        f'"{exemplar.obra.titulo}" por '
        f"{emprestimo.usuario.username}."
    )

    if multa:
        descricao += (
            f" Atraso de {multa.dias_atraso} dia(s), "
            f"multa de R$ {multa.valor_total}."
        )

    registrar_auditoria(
        usuario=funcionario,
        acao=RegistroAuditoria.Acao.DEVOLUCAO,
        entidade="Empréstimo",
        objeto_id=emprestimo.id,
        descricao=descricao,
        endereco_ip=endereco_ip,
    )

    return emprestimo, multa, promovida


@transaction.atomic
def expirar_reserva(reserva):
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

    reserva.status = Reserva.Status.EXPIRADA
    reserva.finalizada_em = timezone.now()

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
    identificadores = list(
        Reserva.objects.filter(
            status=Reserva.Status.AGUARDANDO_RETIRADA,
            expira_em__lte=timezone.now(),
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