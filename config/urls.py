from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path(
        "admin/",
        RedirectView.as_view(
            pattern_name="gestao_dashboard",
            permanent=False,
        ),
    ),
    path("", include("biblioteca.urls")),
]