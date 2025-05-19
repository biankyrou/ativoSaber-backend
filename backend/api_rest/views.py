from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Ativo, Usuario
from .serializers import AtivoSerializer, UsuarioSerializer
from rest_framework import generics
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UsuarioCreateView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioListView(generics.ListAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]  


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_ativos(request):
    nome = request.GET.get('nome')
    ativos = Ativo.objects.filter(usuario=request.user)

    if nome:
        ativos = ativos.filter(nome__icontains=nome)

    serializer = AtivoSerializer(ativos, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consultar_ativo_por_id(request, pk):
    """
    Retorna os dados de um ativo específico baseado no ID, somente se pertence ao usuário logado.
    """
    ativo = get_object_or_404(Ativo, pk=pk, usuario=request.user)
    serializer = AtivoSerializer(ativo)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consultar_ativo_por_nome(request, nome):
    """
    Retorna todos os ativos com o nome informado, do usuário logado.
    """
    ativos = Ativo.objects.filter(nome__icontains=nome, usuario=request.user)
    if not ativos.exists():
        return Response({'mensagem': 'Nenhum ativo encontrado com esse nome.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = AtivoSerializer(ativos, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_ativo(request):
    """
    Cria um novo ativo associado ao usuário logado.
    """
    serializer = AtivoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(usuario=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def atualizar_ativo(request, pk):
    """
    Atualiza um ativo existente somente se pertence ao usuário logado.
    PUT: atualização completa.
    PATCH: atualização parcial.
    """
    ativo = get_object_or_404(Ativo, pk=pk, usuario=request.user)

    parcial = request.method == 'PATCH'
    serializer = AtivoSerializer(ativo, data=request.data, partial=parcial)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deletar_ativo(request, pk):
    """
    Remove um ativo existente somente se pertence ao usuário logado.
    """
    ativo = get_object_or_404(Ativo, pk=pk, usuario=request.user)
    ativo.delete()
    return Response({'mensagem': 'Ativo deletado com sucesso.'}, status=status.HTTP_204_NO_CONTENT)
