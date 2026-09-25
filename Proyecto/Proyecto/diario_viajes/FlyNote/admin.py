from django.contrib import admin
from .models import Viaje

@admin.register(Viaje)
class ViajeAdmin(admin.ModelAdmin):
	list_display = ('destino', 'pais', 'usuario', 'fecha_inicio', 'fecha_termino', 'estado')
	list_filter = ('estado',)
	search_fields = ('destino', 'pais', 'usuario__username')
