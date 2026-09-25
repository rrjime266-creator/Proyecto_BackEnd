"""
URL configuration for diario_viajes project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from FlyNote import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('crear-cuenta/', views.crear_cuenta, name='crear_cuenta'),
    path('recuperar-contrasena/', views.recuperar_contraseña, name='recuperar_contraseña'),
    path('usuario/', views.usuario, name='usuario'),
    path('admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('admin/usuarios/<int:usuario_id>/viajes/', views.admin_ver, name='admin_ver'),
    path('admin/usuarios/<int:usuario_id>/eliminar/', views.admin_eliminar_usuario, name='admin_eliminar_usuario'),
    path('admin/viajes/<int:viaje_id>/editar/', views.admin_editar_viaje, name='admin_editar_viaje'),
    path('admin/viajes/<int:viaje_id>/eliminar/', views.admin_eliminar_viaje, name='admin_eliminar_viaje'),
    path('admin/usuarios/<int:usuario_id>/hacer-admin/', views.cambiar_permiso_admin, name='cambiar_permiso_admin'),
    path('crear-viaje/', views.crear_viaje, name='crear_viaje'),
    path('editar-viaje/<int:viaje_id>/', views.editar_viaje, name='editar_viaje'),
    path('eliminar-viaje/<int:viaje_id>/', views.eliminar_viaje, name='eliminar_viaje'),
    path('cerrar-sesion/', views.cerrar_sesion, name='cerrar_sesion'),
    path('eliminar-cuenta/', views.eliminar_cuenta, name='eliminar_cuenta'),
    path('admin/', admin.site.urls),
]
