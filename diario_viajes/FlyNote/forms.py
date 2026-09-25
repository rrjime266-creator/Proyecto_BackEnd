from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Viaje


class CrearCuentaForm(UserCreationForm):
	email = forms.EmailField(label='Correo electrónico (opcional)', required=False)

	class Meta:
		model = User
		fields = ('username', 'email', 'password1', 'password2')
		labels = {
			'username': 'Nombre de usuario',
		}

	def clean_username(self):
		username = self.cleaned_data.get('username', '').strip()
		if User.objects.filter(username__iexact=username).exists():
			raise forms.ValidationError('Este nombre de usuario ya está registrado.')
		return username

	def clean_email(self):
		email = self.cleaned_data.get('email', '').lower()
		if not email:
			return email
		if User.objects.filter(email__iexact=email).exists():
			raise forms.ValidationError('Este correo ya está registrado.')
		return email


class ViajeForm(forms.ModelForm):
	def __init__(self, *args, editar=False, **kwargs):
		super().__init__(*args, **kwargs)
		if editar:
			self.fields['fecha_inicio'].required = False
			self.fields['fecha_termino'].required = False

	def clean_fecha_inicio(self):
		return self.cleaned_data.get('fecha_inicio') or self.instance.fecha_inicio

	def clean_fecha_termino(self):
		return self.cleaned_data.get('fecha_termino') or self.instance.fecha_termino

	class Meta:
		model = Viaje
		fields = ('destino', 'pais', 'fecha_inicio', 'fecha_termino', 'estado', 'notas')
		labels = {
			'destino': 'Destino',
			'pais': 'País',
			'fecha_inicio': 'Fecha de inicio',
			'fecha_termino': 'Fecha de término',
			'estado': 'Estado',
			'notas': 'Notas',
		}
		widgets = {
			'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
			'fecha_termino': forms.DateInput(attrs={'type': 'date'}),
			'notas': forms.Textarea(attrs={'rows': 4}),
		}
