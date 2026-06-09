from django.db import models
from django.conf import settings
from core.middleware import get_current_request

class AuditLog(models.Model):
    """Model to record system actions for security and auditing."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='logs_auditoria', verbose_name='Usuário'
    )
    matricula = models.CharField(max_length=20, verbose_name='Matrícula')
    acao = models.TextField(verbose_name='Ação')
    data = models.DateField(auto_now_add=True, verbose_name='Data')
    hora = models.TimeField(auto_now_add=True, verbose_name='Hora')
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='Endereço IP')

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-data', '-hora']

    def __str__(self):
        return f"{self.matricula} - {self.acao[:50]} em {self.data} {self.hora}"


def get_client_ip(request):
    """Extracts the client IP from the request metadata."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_action(user, action):
    """
    Saves an audit log entry.
    Automatically retrieves current request from thread storage if available
    to obtain IP address and fallback user/matricula info.
    """
    request = get_current_request()
    ip = get_client_ip(request)

    # Fallback to current request user if user is not provided
    if not user and request and request.user.is_authenticated:
        user = request.user

    matricula = user.matricula if user else 'Sistema'

    AuditLog.objects.create(
        usuario=user,
        matricula=matricula,
        acao=action,
        ip=ip
    )
