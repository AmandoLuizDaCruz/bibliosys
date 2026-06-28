from django.contrib.auth import get_user_model
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
)
from django.urls import reverse_lazy

User = get_user_model()


class CustomPasswordResetView(PasswordResetView):
    template_name = 'biblioteca/autenticacao/password_reset.html'
    email_template_name = 'biblioteca/autenticacao/password_reset_email.html'
    subject_template_name = 'biblioteca/autenticacao/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'biblioteca/autenticacao/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
