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

    class Meta:
        model = Ativo
        fields = '__all__'
        read_only_fields = ['usuario'] 

    def get_rendimento_esperado(self, obj):
        return obj.rendimento_esperado


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


