from django.core.exceptions import ValidationError
from django.test import TestCase
from datetime import date, timedelta
from decimal import Decimal

from .models import Usuario, Ativo


class AtivoValidationTest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='teste@example.com',
            nome='Usuário Teste',
            password='senha123'
        )
        self.data_emissao = date.today()
        self.data_vencimento = self.data_emissao + timedelta(days=365)

    def criar_ativo_valido(self, **kwargs):
        """
        Retorna um ativo com dados válidos. Permite sobrescrever atributos.
        """
        dados = {
            'usuario': self.usuario,
            'nome': 'CDB Banco X',
            'tipo': 'renda_fixa_bancaria',
            'emissor': 'Banco X',
            'tipo_negociacao': 'bolsa',
            'valor_unitario': Decimal('1000.00'),
            'tipo_juros': 'prefixado',
            'taxa_fixa': Decimal('10.00'),
            'indexador': None,
            'percentual_sobre_indexador': None,
            'data_emissao': self.data_emissao,
            'data_vencimento': self.data_vencimento,
            'liquidez': 'diaria',
            'possuiImposto': False,
            'aliquotaImposto': None,
        }
        dados.update(kwargs)
        return Ativo(**dados)

    ## ✅ TESTES DE DATAS

    def test_data_vencimento_anterior_a_emissao(self):
        ativo = self.criar_ativo_valido(data_vencimento=self.data_emissao - timedelta(days=1))
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('data_vencimento', context.exception.message_dict)

    ## ✅ TESTES DE VALOR UNITÁRIO

    def test_valor_unitario_invalido_zero(self):
        ativo = self.criar_ativo_valido(valor_unitario=Decimal('0'))
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('valor_unitario', context.exception.message_dict)

    def test_valor_unitario_invalido_negativo(self):
        ativo = self.criar_ativo_valido(valor_unitario=Decimal('-100'))
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('valor_unitario', context.exception.message_dict)

    ## ✅ TESTES TIPO DE JUROS - PREFIXADO

    def test_prefixado_sem_taxa_fixa(self):
        ativo = self.criar_ativo_valido(taxa_fixa=None)
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('taxa_fixa', context.exception.message_dict)

    def test_prefixado_com_indexador_errado(self):
        ativo = self.criar_ativo_valido(indexador='CDI')
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('indexador', context.exception.message_dict)

    ## ✅ TESTES TIPO DE JUROS - POSFIXADO

    def test_posfixado_sem_indexador(self):
        ativo = self.criar_ativo_valido(
            tipo_juros='posfixado',
            taxa_fixa=None,
            indexador=None,
            percentual_sobre_indexador=Decimal('110')
        )
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('indexador', context.exception.message_dict)

    def test_posfixado_sem_percentual_sobre_indexador(self):
        ativo = self.criar_ativo_valido(
            tipo_juros='posfixado',
            taxa_fixa=None,
            indexador='CDI',
            percentual_sobre_indexador=None
        )
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('percentual_sobre_indexador', context.exception.message_dict)

    def test_posfixado_com_taxa_fixa_errada(self):
        ativo = self.criar_ativo_valido(
            tipo_juros='posfixado',
            taxa_fixa=Decimal('10'),
            indexador='CDI',
            percentual_sobre_indexador=Decimal('110')
        )
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('taxa_fixa', context.exception.message_dict)

    ## ✅ TESTES TIPO DE JUROS - HÍBRIDO

    def test_hibrido_sem_taxa_fixa(self):
        ativo = self.criar_ativo_valido(
            tipo_juros='hibrido',
            taxa_fixa=None,
            indexador='CDI',
            percentual_sobre_indexador=Decimal('110')
        )
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('taxa_fixa', context.exception.message_dict)

    def test_hibrido_sem_indexador(self):
        ativo = self.criar_ativo_valido(
            tipo_juros='hibrido',
            taxa_fixa=Decimal('5'),
            indexador=None,
            percentual_sobre_indexador=Decimal('110')
        )
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('indexador', context.exception.message_dict)

    def test_hibrido_sem_percentual_sobre_indexador(self):
        ativo = self.criar_ativo_valido(
            tipo_juros='hibrido',
            taxa_fixa=Decimal('5'),
            indexador='CDI',
            percentual_sobre_indexador=None
        )
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('percentual_sobre_indexador', context.exception.message_dict)


    ## ✅ TESTES DE IMPOSTO
    def test_possuiImposto_sem_aliquota(self):
        ativo = self.criar_ativo_valido(possuiImposto=True, aliquotaImposto=None)
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('aliquotaImposto', context.exception.message_dict)

    def test_aliquotaImposto_maior_que_100(self):
        ativo = self.criar_ativo_valido(possuiImposto=True, aliquotaImposto=Decimal('150'))
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('aliquotaImposto', context.exception.message_dict)

    def test_aliquotaImposto_informada_sem_possuiImposto(self):
        ativo = self.criar_ativo_valido(possuiImposto=False, aliquotaImposto=Decimal('10'))
        with self.assertRaises(ValidationError) as context:
            ativo.clean()
        self.assertIn('aliquotaImposto', context.exception.message_dict)

