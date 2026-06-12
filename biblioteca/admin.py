from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.core.exceptions import PermissionDenied

from .models import (
    Leitor,
    NotificacaoAdmin,
    Obra,
    SolicitacaoFuncionario,
)


User = get_user_model()
USUARIO_ADMIN_FIXO = "Admin"


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdminProtegido(DjangoUserAdmin):
    def usuario_fixo(self, obj):
        return (
            obj is not None
            and obj.username.casefold()
            == USUARIO_ADMIN_FIXO.casefold()
        )

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        if self.usuario_fixo(obj):
            return False

        return super().has_change_permission(
            request,
            obj,
        )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        if self.usuario_fixo(obj):
            return False

        return super().has_delete_permission(
            request,
            obj,
        )

    def delete_model(self, request, obj):
        if self.usuario_fixo(obj):
            messages.error(
                request,
                "O usuário Admin não pode ser excluído.",
            )
            return

        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        queryset = queryset.exclude(
            username__iexact=USUARIO_ADMIN_FIXO
        )

        super().delete_queryset(
            request,
            queryset,
        )


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "autor",
        "isbn",
        "categoria",
        "quantidade",
    )

    search_fields = (
        "titulo",
        "autor",
        "isbn",
    )


@admin.register(Leitor)
class LeitorAdmin(admin.ModelAdmin):
    list_display = (
        "nome_completo",
        "cpf",
        "email",
        "tipo_vinculo",
        "ativo",
        "usuario",
    )

    search_fields = (
        "nome_completo",
        "cpf",
        "email",
        "usuario__username",
    )

    list_filter = (
        "tipo_vinculo",
        "ativo",
    )


@admin.action(
    description="Aprovar solicitações selecionadas"
)
def aprovar_solicitacoes(
    modeladmin,
    request,
    queryset,
):
    if not request.user.is_superuser:
        raise PermissionDenied

    quantidade = 0

    for solicitacao in queryset.filter(
        status=SolicitacaoFuncionario.Status.PENDENTE
    ):
        solicitacao.aprovar(request.user)
        quantidade += 1

    messages.success(
        request,
        f"{quantidade} solicitação(ões) aprovada(s).",
    )


@admin.action(
    description="Recusar solicitações selecionadas"
)
def recusar_solicitacoes(
    modeladmin,
    request,
    queryset,
):
    if not request.user.is_superuser:
        raise PermissionDenied

    quantidade = 0

    for solicitacao in queryset.filter(
        status=SolicitacaoFuncionario.Status.PENDENTE
    ):
        solicitacao.recusar(request.user)
        quantidade += 1

    messages.success(
        request,
        f"{quantidade} solicitação(ões) recusada(s).",
    )


@admin.register(SolicitacaoFuncionario)
class SolicitacaoFuncionarioAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "status",
        "criada_em",
        "analisada_em",
        "analisada_por",
    )

    list_filter = (
        "status",
        "criada_em",
    )

    search_fields = (
        "usuario__username",
        "usuario__email",
    )

    readonly_fields = (
        "usuario",
        "status",
        "criada_em",
        "analisada_em",
        "analisada_por",
    )

    actions = (
        aprovar_solicitacoes,
        recusar_solicitacoes,
    )

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(
        self,
        request,
        obj=None,
    ):
        return request.user.is_superuser

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False


@admin.action(
    description="Marcar notificações como lidas"
)
def marcar_como_lidas(
    modeladmin,
    request,
    queryset,
):
    if not request.user.is_superuser:
        raise PermissionDenied

    queryset.update(lida=True)


@admin.register(NotificacaoAdmin)
class NotificacaoAdminAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "solicitacao",
        "criada_em",
        "lida",
    )

    list_filter = (
        "lida",
        "criada_em",
    )

    readonly_fields = (
        "solicitacao",
        "titulo",
        "mensagem",
        "criada_em",
        "lida",
    )

    actions = (
        marcar_como_lidas,
    )

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(
        self,
        request,
        obj=None,
    ):
        return request.user.is_superuser

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return request.user.is_superuser