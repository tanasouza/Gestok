// gestok.js

document.addEventListener('DOMContentLoaded', function() {
    // Mantem os filtros de periodo em uma faixa cronologica valida.
    document.querySelectorAll('.gestok-filter-form').forEach(function(form) {
        const startInput = form.querySelector('input[name="data_inicio"]');
        const endInput = form.querySelector('input[name="data_fim"]');

        if (!startInput || !endInput) return;

        function syncDateRange() {
            startInput.max = endInput.value || '';
            endInput.min = startInput.value || '';

            const invalidRange = Boolean(
                startInput.value &&
                endInput.value &&
                endInput.value < startInput.value
            );

            endInput.setCustomValidity(
                invalidRange
                    ? 'A data final deve ser igual ou posterior à data inicial.'
                    : ''
            );
        }

        startInput.addEventListener('input', syncDateRange);
        startInput.addEventListener('change', syncDateRange);
        endInput.addEventListener('input', syncDateRange);
        endInput.addEventListener('change', syncDateRange);
        form.addEventListener('submit', function(event) {
            syncDateRange();
            if (!form.checkValidity()) {
                event.preventDefault();
                form.reportValidity();
            }
        });

        syncDateRange();
    });
    // 1. Auto-dismiss de alerts após 5s
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (typeof bootstrap !== 'undefined') {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        }, 5000);
    });

    // 2. Confirmar ações destrutivas (estorno, desativação)
    const confirmActions = document.querySelectorAll('[data-confirm]');
    confirmActions.forEach(function(element) {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Tem certeza que deseja realizar esta ação?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // 3. Toggle mostrar/ocultar senha
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            if (targetInput) {
                const type = targetInput.getAttribute('type') === 'password' ? 'text' : 'password';
                targetInput.setAttribute('type', type);

                // Toggle icon
                const icon = this.querySelector('i');
                if (icon) {
                    if (type === 'password') {
                        icon.classList.remove('bi-eye-slash');
                        icon.classList.add('bi-eye');
                    } else {
                        icon.classList.remove('bi-eye');
                        icon.classList.add('bi-eye-slash');
                    }
                }
            }
        });
    });

    // 4. Meter de força de senha
    const passwordInput = document.getElementById('id_new_password');
    const strengthBar = document.getElementById('password-strength-bar');
    const strengthText = document.getElementById('password-strength-text');

    if (passwordInput && strengthBar && strengthText) {
        passwordInput.addEventListener('input', function() {
            const value = this.value;
            let strength = 0;

            if (value.length >= 6) strength += 20;
            if (value.length >= 10) strength += 20;
            if (/[A-Z]/.test(value)) strength += 20;
            if (/[0-9]/.test(value)) strength += 20;
            if (/[^A-Za-z0-9]/.test(value)) strength += 20;

            strengthBar.style.width = strength + '%';

            if (strength === 0) {
                strengthBar.className = 'strength-meter-bar';
                strengthText.textContent = '';
            } else if (strength <= 40) {
                strengthBar.className = 'strength-meter-bar bg-danger';
                strengthText.textContent = 'Fraca';
                strengthText.className = 'text-danger fw-semibold';
            } else if (strength <= 80) {
                strengthBar.className = 'strength-meter-bar bg-warning';
                strengthText.textContent = 'Média';
                strengthText.className = 'text-warning fw-semibold';
            } else {
                strengthBar.className = 'strength-meter-bar bg-success';
                strengthText.textContent = 'Forte';
                strengthText.className = 'text-success fw-semibold';
            }
        });
    }



    // 6. Chart.js para Vendas Anuais
    const chartCanvas = document.getElementById('chartVendasAnuais');
    const dadosScript = document.getElementById('dados-grafico');

    if (chartCanvas && dadosScript) {
        try {
            const dados = JSON.parse(dadosScript.textContent);

            // Verifica melhor e pior mes para cores
            const maxValue = Math.max(...dados);
            // Ignore zeros para pior mes se possivel, ou apenas pega o minimo real
            const validValues = dados.filter(v => v > 0);
            const minValue = validValues.length > 0 ? Math.min(...validValues) : 0;

            const backgroundColors = dados.map(valor => {
                if (valor === 0) return '#64748B'; // secondary
                if (valor === maxValue) return '#16A34A'; // success (melhor)
                if (valor === minValue) return '#DC2626'; // danger (pior)
                return '#2563EB'; // primary (normal)
            });

            const ctx = chartCanvas.getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
                    datasets: [{
                        label: 'Faturamento Mensal',
                        data: dados,
                        backgroundColor: backgroundColors,
                        borderRadius: 6,
                        borderWidth: 0,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        label += new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(context.parsed.y);
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return 'R$ ' + value.toLocaleString('pt-BR');
                                }
                            }
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Erro ao inicializar Chart.js:', e);
        }
    }
});
