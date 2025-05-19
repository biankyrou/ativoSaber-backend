from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, password=None):
        if not email:
            raise ValueError("O email é obrigatório")
        email = self.normalize_email(email)
        usuario = self.model(email=email, nome=nome)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, nome, password=None):
        usuario = self.create_user(email, nome, password)
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save(using=self._db)
        return usuario

class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)  
    email = models.EmailField(unique=True)   
    nome = models.CharField(max_length=150, default='')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    def __str__(self):
        return self.nome



TIPOS_ATIVO = [
    ('renda_fixa_bancaria', 'Renda Fixa Bancária (CDB, LCI, LCA)'),
    ('titulos_publicos', 'Títulos Públicos (Tesouro Direto)'),
    ('debentures_creditos', 'Debêntures e Créditos (Debêntures, CRI, CRA)'),
]

TIPOS_NEGOCIACAO = [
    ('bolsa', 'Bolsa'),
    ('balcao', 'Balcão'),
]

TIPOS_JUROS = [
    ('prefixado', 'Prefixado'),
    ('posfixado', 'Pós-fixado'),
    ('hibrido', 'Híbrido'),
]

TIPOS_LIQUIDEZ = [
    ('diaria', 'Diária'),
    ('apos_vencimento', 'Após Vencimento'),
]

STATUS_ATIVO = [
    ('ativo', 'Ativo'),
    ('resgatado', 'Resgatado'),
    ('vencido', 'Vencido'),
]

class Ativo(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)  # Relacionamento com o usuário (banco)
    nome = models.CharField(max_length=150)  # Nome do ativo, e.g., "CDB Banco XP 2025"
    tipo = models.CharField(max_length=50, choices=TIPOS_ATIVO)

    emissor = models.CharField(max_length=150, blank=True, null=True)  # Nome do banco/empresa/governo emissor
    tipo_negociacao = models.CharField(max_length=20, choices=TIPOS_NEGOCIACAO, default='bolsa') 
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    taxa_rentabilidade = models.DecimalField(max_digits=5, decimal_places=2, help_text="Em percentual (%)")
    tipo_juros = models.CharField(max_length=50, choices=TIPOS_JUROS)

    data_emissao = models.DateField()
    data_vencimento = models.DateField()
    liquidez = models.CharField(max_length=50, choices=TIPOS_LIQUIDEZ)

    isento_impostos = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=STATUS_ATIVO, default='ativo')

    def __str__(self):
        return f'{self.nome} | {self.get_tipo_display()} | {self.valor_unitario} | {self.status}'
    
    @property
    def rendimento_esperado(self):
        """
        Calcula o rendimento esperado com base no valor unitário e na taxa de rentabilidade.
        A fórmula é: rendimento_esperado = valor_unitario * (taxa_rentabilidade / 100)
        """
        return self.valor_unitario * (self.taxa_rentabilidade / 100)
    
    def clean(self):
        errors = {}

        if self.data_vencimento <= self.data_emissao:
            errors['data_vencimento'] = "A data de vencimento deve ser posterior à data de emissão."

        if self.valor_unitario <= 0:
            errors['valor_unitario'] = "O valor unitário deve ser maior que zero."

        if not (0 <= self.taxa_rentabilidade <= 100):
            errors['taxa_rentabilidade'] = "A taxa de rentabilidade deve estar entre 0% e 100%."

        if self.isento_impostos and self.tipo != 'renda_fixa_bancaria':
            errors['isento_impostos'] = "Somente ativos de renda fixa bancária podem ser isentos de impostos."

        if self.status in ['vencido', 'resgatado']:
            if self.data_vencimento > timezone.now().date():
                errors['status'] = f"Não é possível marcar como '{self.status}' antes do vencimento."

        if errors:
            raise ValidationError(errors)
