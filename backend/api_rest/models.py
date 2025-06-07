from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from datetime import date
from decimal import Decimal

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

INDEXADORES = [
    ('CDI', 'CDI'),
    ('SELIC', 'SELIC'),
    ('IPCA', 'IPCA'),
    ('IGPM', 'IGPM'),
]

INDEXADORES_VALORES = {
    'CDI': Decimal('0.13'),
    'SELIC': Decimal('0.12'),
    'IPCA': Decimal('0.04'),
    'IGPM': Decimal('0.06'),
}

class Ativo(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    nome = models.CharField(max_length=150)
    tipo = models.CharField(max_length=50, choices=TIPOS_ATIVO)
    emissor = models.CharField(max_length=150, blank=True, null=True)
    tipo_negociacao = models.CharField(max_length=20, choices=TIPOS_NEGOCIACAO, default='bolsa')
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    quantidade = models.IntegerField()
    tipo_juros = models.CharField(max_length=50, choices=TIPOS_JUROS)

    # Campos de rentabilidade
    taxa_fixa = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Taxa fixa anual em percentual (%)."
    )
    indexador = models.CharField(
        max_length=10, choices=INDEXADORES,
        null=True, blank=True,
        help_text="Indexador econômico (CDI, SELIC, IPCA, etc.)."
    )
    percentual_sobre_indexador = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Percentual sobre o indexador (Ex.: 110% CDI)."
    )

    data_emissao = models.DateField()
    data_vencimento = models.DateField()

    liquidez = models.CharField(max_length=50, choices=TIPOS_LIQUIDEZ)

    possuiImposto = models.BooleanField(default=False)
    aliquotaImposto = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Percentual de imposto sobre o rendimento (ex: 15 para 15%)."
    )

    def __str__(self):
        return f'{self.nome} | {self.get_tipo_display()} | {self.valor_unitario}'

    def clean(self):
        errors = {}

        if self.data_vencimento <= self.data_emissao:
            errors['data_vencimento'] = "A data de vencimento deve ser posterior à data de emissão."

        if self.valor_unitario <= 0:
            errors['valor_unitario'] = "O valor unitário deve ser maior que zero."

        # Validação para tipos de juros
        if self.tipo_juros == 'prefixado':
            if self.taxa_fixa is None:
                errors['taxa_fixa'] = "Para ativos prefixados, a taxa fixa é obrigatória."
            if self.indexador or self.percentual_sobre_indexador:
                errors['indexador'] = "Ativos prefixados não devem ter indexador nem percentual sobre indexador."

        elif self.tipo_juros == 'posfixado':
            if not self.indexador:
                errors['indexador'] = "Para ativos pós-fixados, o indexador é obrigatório."
            if self.percentual_sobre_indexador is None:
                errors['percentual_sobre_indexador'] = "Informe o percentual sobre o indexador."
            if self.taxa_fixa:
                errors['taxa_fixa'] = "Ativos pós-fixados não devem ter taxa fixa."

        elif self.tipo_juros == 'hibrido':
            if self.taxa_fixa is None:
                errors['taxa_fixa'] = "A taxa fixa é obrigatória em ativos híbridos."
            if not self.indexador:
                errors['indexador'] = "O indexador é obrigatório em ativos híbridos."
            if self.percentual_sobre_indexador is None:
                errors['percentual_sobre_indexador'] = "O percentual sobre o indexador é obrigatório em ativos híbridos."

        if self.possuiImposto:
            if self.aliquotaImposto is None:
                errors['aliquotaImposto'] = "Informe a alíquota de imposto para ativos tributados."
            elif not (0 <= self.aliquotaImposto <= 100):
                errors['aliquotaImposto'] = "A alíquota de imposto deve estar entre 0 e 100."
        else:
            if self.aliquotaImposto is not None:
                errors['aliquotaImposto'] = "A alíquota de imposto deve ser vazia se o ativo não possuir imposto."


        if errors:
            raise ValidationError(errors)
        
    def periodo_em_anos(self):
        if self.data_vencimento and self.data_emissao:
            dias = (self.data_vencimento - self.data_emissao).days
            return round(dias / 365.25, 6)
        return None

    def rendimento_esperado(self):
        """
        Simula o rendimento bruto após um período (em anos) e já desconta imposto (se aplicável).

        - Prefixado: valor * (1 + taxa_fixa) ** periodo
        - Pós-fixado: valor * (1 + percentual_indexador * CDI) ** periodo
        - Híbrido: valor * (1 + taxa_fixa + percentual_indexador * indexador) ** periodo

        Obs.: indexadores fixos, podem ser atualizados via API.

        O rendimento retornado já considera o desconto do imposto, caso possuaImposto seja True.
        """

        periodo = self.periodo_em_anos()
        if periodo is None:
            return None

        periodo = Decimal(str(periodo))
        valor = self.valor_unitario * self.quantidade

        if self.tipo_juros == 'prefixado':
            if self.taxa_fixa is None:
                return None
            taxa = self.taxa_fixa / Decimal('100')
            rendimento_bruto = valor * (1 + taxa) ** periodo

        elif self.tipo_juros == 'posfixado':
            if not self.indexador or self.percentual_sobre_indexador is None:
                return None
            taxa_indexador = INDEXADORES_VALORES.get(self.indexador, Decimal('0.10'))
            taxa = (self.percentual_sobre_indexador / Decimal('100')) * taxa_indexador
            rendimento_bruto = valor * (1 + taxa) ** periodo

        elif self.tipo_juros == 'hibrido':
            if self.taxa_fixa is None or not self.indexador or self.percentual_sobre_indexador is None:
                return None
            taxa_indexador = INDEXADORES_VALORES.get(self.indexador, Decimal('0.10'))
            taxa_fixa = self.taxa_fixa / Decimal('100')
            taxa_variavel = (self.percentual_sobre_indexador / Decimal('100')) * taxa_indexador
            taxa_total = taxa_fixa + taxa_variavel
            rendimento_bruto = valor * (1 + taxa_total) ** periodo

        else:
            return None

        if self.possuiImposto and self.aliquotaImposto is not None:
            aliquota = self.aliquotaImposto / Decimal('100')
            imposto = rendimento_bruto * aliquota
            rendimento_liquido = rendimento_bruto - imposto
        else:
            rendimento_liquido = rendimento_bruto

        return rendimento_liquido

    
    def calcular_resgate(self, data_resgate=None):
        """
        Calcula o valor acumulado considerando juros compostos.

        Sem impostos, taxas ou IOF.

        Args:
            data_resgate (date): Data de resgate (padrão: hoje)

        Returns:
            dict: {
                'valor_acumulado': Decimal,
                'dias_corridos': int,
                'rendimento': Decimal
            }
            ou None se dados insuficientes
        """

        if self.liquidez != 'diaria':
            return None  # Ou lançar ValidationError, conforme o caso
    
        if not data_resgate:
            data_resgate = date.today()

        if data_resgate < self.data_emissao:
            return None  

        if data_resgate > self.data_vencimento:
            data_resgate = self.data_vencimento  

        dias_corridos = (data_resgate - self.data_emissao).days
        periodo_anos = Decimal(str(dias_corridos / 365.25))

        valor_atual = self.valor_unitario * self.quantidade

        if self.tipo_juros == 'prefixado' and self.taxa_fixa is not None:
            taxa_anual = self.taxa_fixa / Decimal('100')
            valor_atual *= (1 + taxa_anual) ** periodo_anos

        elif self.tipo_juros == 'posfixado' and self.indexador and self.percentual_sobre_indexador is not None:
            taxa_indexador = INDEXADORES_VALORES.get(self.indexador, Decimal('0.10'))
            taxa_efetiva = (self.percentual_sobre_indexador / Decimal('100')) * taxa_indexador
            valor_atual *= (1 + taxa_efetiva) ** periodo_anos

        elif self.tipo_juros == 'hibrido' and all([self.taxa_fixa is not None, self.indexador, self.percentual_sobre_indexador is not None]):
            taxa_indexador = INDEXADORES_VALORES.get(self.indexador, Decimal('0.10'))
            taxa_fixa = self.taxa_fixa / Decimal('100')
            taxa_variavel = (self.percentual_sobre_indexador / Decimal('100')) * taxa_indexador
            taxa_total = taxa_fixa + taxa_variavel
            valor_atual *= (1 + taxa_total) ** periodo_anos

        else:
            return None  

        valor_atual = valor_atual.quantize(Decimal('0.01'))

        return {
            'valor_acumulado': valor_atual,
            'dias_corridos': dias_corridos,
            'rendimento': (valor_atual - (self.valor_unitario * self.quantidade)).quantize(Decimal('0.01'))
        }
    
    @property
    def valor_investido(self):
        return self.valor_unitario * self.quantidade

