from django.urls import path
from . import views
from .views import UsuarioCreateView, UsuarioListView, CustomTokenObtainPairView

urlpatterns = [
    path('usuarios/', UsuarioCreateView.as_view(), name='usuario-create'),
    path('usuarios/lista/', UsuarioListView.as_view(), name='usuario-list'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('ativos/', views.listar_ativos, name='listar_ativos'),
    path('ativos/<int:pk>/', views.consultar_ativo_por_id, name='consultar_ativo_por_id'),
    path('ativos/nome/<str:nome>/', views.consultar_ativo_por_nome, name='consultar_ativo_por_nome'),
    path('ativos/criar/', views.criar_ativo, name='criar_ativo'),
    path('ativos/atualizar/<int:pk>/', views.atualizar_ativo, name='atualizar_ativo'),
    path('ativos/deletar/<int:pk>/', views.deletar_ativo, name='deletar_ativo'),
]
