from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, password=None, **extra_fields):
        email = self.normalize_email(email) if email else ''
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_password('senha123')
        user.save(using=self._db)
        return user

    def create_superuser(self, matricula, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('perfil', 'ADMINISTRADOR')
        extra_fields.setdefault('primeiro_acesso', False)
        extra_fields.setdefault('cargo', 'Gerente')
        extra_fields.setdefault('nome_completo', 'Administrador')

        user = self.model(matricula=matricula, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    PERFIL_CHOICES = (
        ('ADMINISTRADOR', 'Administrador'),
        ('VENDAS', 'Atendente de Vendas'),
        ('CAIXA', 'Operador de Caixa'),
        ('ESTOQUE', 'Operador de Estoque'),
    )

    CARGO_CHOICES = (
        ('Gerente', 'Gerente'),
        ('Atendente', 'Atendente'),
        ('Estoquista', 'Estoquista'),
    )

    CARGOS_ADMINISTRATIVOS = {'Gerente'}
    CARGOS_CAIXA = {'Atendente'}
    CARGOS_VENDAS = {'Atendente'}

    matricula = models.CharField(max_length=20, unique=True, db_index=True)
    nome_completo = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    cargo = models.CharField(max_length=100, choices=CARGO_CHOICES)
    perfil = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='VENDAS')
    primeiro_acesso = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'matricula'
    REQUIRED_FIELDS = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} ({self.matricula})"

    def get_full_name(self):
        return self.nome_completo

    def get_short_name(self):
        return self.nome_completo.split()[0] if self.nome_completo else ""

    @property
    def nome_cabecalho(self):
        parts = self.nome_completo.split()
        if not parts:
            return self.matricula
        if len(parts) == 1:
            return parts[0]
        return f'{parts[0]} {parts[-1][0].upper()}.'

    @classmethod
    def perfil_para_cargo(cls, cargo):
        if cargo in cls.CARGOS_ADMINISTRATIVOS:
            return 'ADMINISTRADOR'
        if cargo == 'Estoquista':
            return 'ESTOQUE'
        return 'VENDAS'

    @property
    def perfil_operacional(self):
        return 'ADMINISTRADOR' if self.is_superuser else self.perfil_para_cargo(self.cargo)

    @property
    def eh_administrador(self):
        return self.perfil_operacional == 'ADMINISTRADOR'

    @property
    def pode_vender(self):
        return self.perfil_operacional in {'ADMINISTRADOR', 'VENDAS'}

    @property
    def pode_operar_caixa(self):
        return self.eh_administrador or self.cargo == 'Atendente'

    @property
    def pode_ver_movimentacoes(self):
        return self.eh_administrador or self.cargo == 'Atendente'

    @property
    def pode_ver_produtos(self):
        return self.eh_administrador or self.cargo == 'Estoquista'

    @property
    def pagina_inicial(self):
        if self.eh_administrador:
            return 'reports:dashboard'
        if self.cargo == 'Estoquista':
            return 'products:product_list'
        return 'sales:my_sales'

    @property
    def endereco_formatado(self):
        if not self.endereco:
            return ""
        return self.endereco.replace(' | ', ', ')

    def save(self, *args, **kwargs):
        if not self.matricula:
            # We filter for numeric matriculas to avoid any issues
            last_user = CustomUser.objects.filter(matricula__regex=r'^\d+$').order_by('-matricula').first()
            if last_user:
                self.matricula = str(int(last_user.matricula) + 1)
            else:
                self.matricula = '1000'
        # Permissions are derived from the operational role.
        self.perfil = self.perfil_operacional
        # Keep is_active synchronized with ativo
        self.is_active = self.ativo

        update_fields = kwargs.get('update_fields')
        if update_fields:
            update_fields = set(update_fields)
            if 'cargo' in update_fields:
                update_fields.add('perfil')
            if 'ativo' in update_fields:
                update_fields.add('is_active')
            kwargs['update_fields'] = update_fields

        super().save(*args, **kwargs)
