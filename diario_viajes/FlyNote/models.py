from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models

class Viaje(models.Model):
	class Estado(models.TextChoices):
		COMPLETADO = 'completado', 'Completado'
		EN_PROGRESO = 'en_progreso', 'En progreso'
		PLANIFICADO = 'planificado', 'Planificado'

	usuario = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='viajes',
		null=True,
		blank=True,
	)
	destino = models.CharField(max_length=120)
	pais = models.CharField(max_length=100)
	fecha_inicio = models.DateField()
	fecha_termino = models.DateField()
	estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PLANIFICADO)
	notas = models.TextField(blank=True)

	class Meta:
		ordering = ['-fecha_inicio']
		verbose_name = 'viaje'
		verbose_name_plural = 'viajes'

	def __str__(self):
		return f'{self.destino}, {self.pais}'

	def clean(self):
		super().clean()
		if self.fecha_inicio and self.fecha_termino and self.fecha_termino < self.fecha_inicio:
			raise ValidationError({'fecha_termino': 'La fecha de término no puede ser anterior a la fecha de inicio.'})
