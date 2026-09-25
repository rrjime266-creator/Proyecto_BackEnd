from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from functools import wraps

from .forms import CrearCuentaForm, ViajeForm
from .models import Viaje


def usuario_normal_requerido(view):
	@wraps(view)
	def vista(request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect('inicio')
		if request.user.is_staff:
			return redirect('admin_usuarios')
		return view(request, *args, **kwargs)
	return vista


def inicio(request):
	if request.user.is_authenticated:
		return redirect('admin_usuarios' if request.user.is_staff else 'usuario')

	error = None
	if request.method == 'POST':
		identificador = request.POST.get('identificador', '').strip()
		password = request.POST.get('password', '')
		User = get_user_model()
		usuario = User.objects.filter(email__iexact=identificador).first()
		username = usuario.username if usuario else identificador
		user = authenticate(request, username=username, password=password)

		if user is not None:
			login(request, user)
			return redirect('usuario')

		error = 'El usuario o la contraseña no son correctos.'

	return render(request, 'inicio.html', {'error': error})


def recuperar_contraseña(request):
	mensaje = None
	if request.method == 'POST':
		mensaje = 'Si los datos corresponden a una cuenta, recibirás instrucciones para continuar.'
	return render(request, 'recuperar_contraseña.html', {'mensaje': mensaje})


def crear_cuenta(request):
	if request.user.is_authenticated:
		return redirect('admin_usuarios' if request.user.is_staff else 'usuario')

	form = CrearCuentaForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		user = form.save()
		login(request, user)
		return redirect('admin_usuarios' if user.is_staff else 'usuario')

	return render(request, 'crearCuenta.html', {'form': form})


@usuario_normal_requerido
def usuario(request):
	todos_los_viajes = Viaje.objects.filter(usuario=request.user).order_by('-fecha_inicio')
	viajes = todos_los_viajes
	filtro = request.GET.get('estado', 'todos')
	if filtro in Viaje.Estado.values:
		viajes = viajes.filter(estado=filtro)
	else:
		filtro = 'todos'
	return render(request, 'usuario.html', {
		'viajes': viajes,
		'todos_los_viajes': todos_los_viajes,
		'filtro_actual': filtro,
	})


@staff_member_required(login_url='inicio')
def admin_usuarios(request):
	usuarios = get_user_model().objects.filter(is_staff=False).prefetch_related('viajes').order_by('username')
	return render(request, 'admin.html', {'usuarios': usuarios})


@staff_member_required(login_url='inicio')
def admin_ver(request, usuario_id):
	usuario = get_object_or_404(get_user_model(), id=usuario_id, is_staff=False)
	viajes = Viaje.objects.filter(usuario=usuario)
	return render(request, 'adminVer.html', {'usuario': usuario, 'viajes': viajes})


@user_passes_test(lambda user: user.is_superuser, login_url='inicio')
@require_POST
def admin_eliminar_usuario(request, usuario_id):
	usuario = get_object_or_404(get_user_model(), id=usuario_id, is_staff=False)
	usuario.delete()
	return redirect('admin_usuarios')


@staff_member_required(login_url='inicio')
def admin_editar_viaje(request, viaje_id):
	viaje = get_object_or_404(Viaje, id=viaje_id, usuario__is_staff=False)
	form = ViajeForm(request.POST or None, instance=viaje, editar=True)
	if request.method == 'POST' and form.is_valid():
		form.save()
		return redirect('admin_ver', usuario_id=viaje.usuario_id)

	return render(request, 'relacionViaje.html', {
		'form': form,
		'viaje': viaje,
		'es_admin': True,
	})


@require_POST
@staff_member_required(login_url='inicio')
def admin_eliminar_viaje(request, viaje_id):
	viaje = get_object_or_404(Viaje, id=viaje_id, usuario__is_staff=False)
	usuario_id = viaje.usuario_id
	viaje.delete()
	return redirect('admin_ver', usuario_id=usuario_id)


@user_passes_test(lambda user: user.is_superuser, login_url='inicio')
@require_POST
def cambiar_permiso_admin(request, usuario_id):
	usuario = get_object_or_404(get_user_model(), id=usuario_id, is_staff=False)
	usuario.is_staff = True
	usuario.save(update_fields=['is_staff'])
	return redirect('admin_usuarios')

@usuario_normal_requerido
def crear_viaje(request):
	form = ViajeForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		viaje = form.save(commit=False)
		viaje.usuario = request.user
		viaje.save()
		return redirect('usuario')

	return render(request, 'crearViaje.html', {'form': form})


@usuario_normal_requerido
def editar_viaje(request, viaje_id):
	viaje = get_object_or_404(Viaje, id=viaje_id, usuario=request.user)
	form = ViajeForm(request.POST or None, instance=viaje, editar=True)
	if request.method == 'POST' and form.is_valid():
		form.save()
		return redirect('usuario')

	return render(request, 'relacionViaje.html', {'form': form, 'viaje': viaje})


@require_POST
@usuario_normal_requerido
def eliminar_viaje(request, viaje_id):
	viaje = get_object_or_404(Viaje, id=viaje_id, usuario=request.user)
	viaje.delete()
	return redirect('usuario')


@require_POST
@login_required(login_url='inicio')
def cerrar_sesion(request):
	logout(request)
	return redirect('inicio')


@require_POST
@login_required(login_url='inicio')
def eliminar_cuenta(request):
	usuario = request.user
	logout(request)
	usuario.delete()
	return redirect('inicio')
