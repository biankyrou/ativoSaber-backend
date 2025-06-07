from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from .models import Usuario, Ativo


class UsuarioModelTest(TestCase):
    def test_criacao_usuario(self):
        usuario = Usuario.objects.create_user(
            email='teste@exemplo.com', nome='Teste', password='senha123'
        )
        self.assertEqual(usuario.email, 'teste@exemplo.com')
        self.assertTrue(usuario.check_password('senha123'))
        self.assertFalse(usuario.is_staff)

    def test_criacao_superusuario(self):
        admin = Usuario.objects.create_superuser(
            email='admin@exemplo.com', nome='Admin', password='admin123'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AtivoModelTest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='user@exemplo.com', nome='Usuário', password='senha'
        )
        self.data_emissao = date.today()
        self.data_vencimento = self.data_emissao + timedelta(days=365 * 2)  # 2 anos

    def criar_ativo_valido(self, **kwargs):
        """Cria um ativo padrão prefixado válido, podendo sobrescrever campos."""
        defaults = {
            'usuario': self.usuario,
            'nome': 'Ativo Teste',
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
        defaults.update(kwargs)
        return Ativo.objects.create(**defaults)

    # --- Testes de validação ---

    def test_data_vencimento_anterior_data_emissao(self):
        ativo = self.criar_ativo_valido(data_vencimento=self.data_emissao - timedelta(days=1))
        with self.assertRaises(ValidationError):
            ativo.clean()

    def test_valor_unitario_invalido(self):
        ativo = self.criar_ativo_valido(valor_unitario=Decimal('0'))
        with self.assertRaises(ValidationError):
            ativo.clean()

    def test_prefixado_sem_taxa(self):
        ativo = self.criar_ativo_valido(taxa_fixa=None)
        with self.assertRaises(ValidationError):
            ativo.clean()

    def test_posfixado_sem_indexador(self):
        ativo = self.criar_ativo_valido(
            tipo_juros='posfixado',
            taxa_fixa=None,
            indexador=None,
            percentual_sobre_indexador=Decimal('110.00')
        )
        with self.assertRaises(ValidationError):
            ativo.clean()

    def test_hibrido_sem_dados(self):
        ativo = self.criar_ativo_valido(
            tipo_juros='hibrido',
            taxa_fixa=None,
            indexador=None,
            percentual_sobre_indexador=None
        )
        with self.assertRaises(ValidationError):
            ativo.clean()

    def test_possui_imposto_sem_aliquota(self):
        ativo = self.criar_ativo_valido(
            possuiImposto=True,
            aliquotaImposto=None
        )
        with self.assertRaises(ValidationError):
            ativo.clean()

    def test_aliquota_imposto_invalida(self):
        ativo = self.criar_ativo_valido(
            possuiImposto=True,
            aliquotaImposto=Decimal('150.00')
        )
        with self.assertRaises(ValidationError):
            ativo.clean()


    # --- Testes de rendimento ---

    def test_rendimento_prefixado(self):
        ativo = self.criar_ativo_valido()
        esperado = ativo.rendimento_esperado()
        self.assertIsInstance(esperado, Decimal)
        self.assertGreater(esperado, ativo.valor_unitario)

    def test_rendimento_posfixado(self):
        ativo = self.criar_ativo_valido(
            tipo_juros='posfixado',
            taxa_fixa=None,
            indexador='CDI',
            percentual_sobre_indexador=Decimal('110.00')
        )
        esperado = ativo.rendimento_esperado()
        self.assertIsInstance(esperado, Decimal)
        self.assertGreater(esperado, ativo.valor_unitario)

    def test_rendimento_hibrido(self):
        ativo = self.criar_ativo_valido(
            tipo_juros='hibrido',
            taxa_fixa=Decimal('5.00'),
            indexador='IPCA',
            percentual_sobre_indexador=Decimal('110.00')
        )
        esperado = ativo.rendimento_esperado()
        self.assertIsInstance(esperado, Decimal)
        self.assertGreater(esperado, ativo.valor_unitario)

    # --- Testes de cálculo de resgate ---

    def test_calcular_resgate(self):
        ativo = self.criar_ativo_valido()
        resultado = ativo.calcular_resgate(data_resgate=self.data_emissao + timedelta(days=365))
        self.assertIsInstance(resultado, dict)
        self.assertIn('valor_acumulado', resultado)
        self.assertIn('dias_corridos', resultado)
        self.assertIn('rendimento', resultado)

    def test_calcular_resgate_data_antes_emissao(self):
        ativo = self.criar_ativo_valido()
        resultado = ativo.calcular_resgate(data_resgate=self.data_emissao - timedelta(days=10))
        self.assertIsNone(resultado)

    def test_calcular_resgate_apos_vencimento(self):
        ativo = self.criar_ativo_valido()
        data_apos_venc = self.data_vencimento + timedelta(days=10)
        resultado = ativo.calcular_resgate(data_resgate=data_apos_venc)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado['dias_corridos'], (self.data_vencimento - self.data_emissao).days)
