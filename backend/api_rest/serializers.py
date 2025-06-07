from rest_framework import serializers
from .models import Ativo, Usuario
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['nome'] = user.nome  
        return token

class AtivoSerializer(serializers.ModelSerializer):
    rendimento_esperado = serializers.SerializerMethodField()
    valor_investido = serializers.ReadOnlyField()

    class Meta:
        model = Ativo
        fields = '__all__'
        read_only_fields = ['usuario']

    def get_rendimento_esperado(self, obj):
        resultado = obj.rendimento_esperado()
        if resultado is None:
            return None
        return float(resultado)
    
    def get_valor_investido(self, obj):
        return float(obj.valor_investido)

class AtivoNomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ativo
        fields = ['nome']

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['email', 'nome', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = Usuario.objects.create_user(
            email=validated_data['email'],
            nome=validated_data['nome'],
            password=validated_data['password']
        )
        return user
