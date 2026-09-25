document.addEventListener('DOMContentLoaded', function () {
	var toggleButtons = document.querySelectorAll('[data-password-targets]');

	toggleButtons.forEach(function (button) {
		var targetIds = button.dataset.passwordTargets.split(' ');
		var inputs = targetIds
			.map(function (id) { return document.getElementById(id); })
			.filter(Boolean);

		button.addEventListener('click', function () {
			var shouldShow = inputs.some(function (input) { return input.type === 'password'; });

			inputs.forEach(function (input) {
				input.type = shouldShow ? 'text' : 'password';
			});

			button.textContent = shouldShow ? 'Ocultar' : 'Mostrar';
			button.setAttribute('aria-pressed', String(shouldShow));
			button.setAttribute('aria-label', shouldShow ? 'Ocultar contraseña' : 'Mostrar contraseña');
		});
	});
});
