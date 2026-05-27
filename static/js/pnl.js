document.addEventListener("DOMContentLoaded", function() {
    
    // barra
    const btnMenu = document.getElementById('btn-menu');
    const sidebar = document.getElementById('sidebar');
    btnMenu.addEventListener('click', () => {
        sidebar.classList.toggle('fechada');
    });

    // DataTables
    $('#tabDados').DataTable({
        language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json' },
        pageLength: 5,
        order: [[0, 'desc']]
    });

    // Dados da API
    fetch('/api/dados')
        .then(res => res.json())
        .then(d => {
            document.getElementById('txt-total').innerText = d.total + " kg";
            document.getElementById('txt-esc1').innerText = d.esc1 + " kg";
            document.getElementById('txt-esc2').innerText = d.esc2 + " kg";

            // Gráfico de linha
            new Chart(document.getElementById('grafLinha'), {
                type: 'line',
                data: {
                    labels: d.meses,
                    datasets: [{
                        label: 'Total CO2',
                        data: d.co2_totais,
                        borderColor: '#059669',
                        fill: true,
                        backgroundColor: 'rgba(5, 150, 105, 0.1)',
                        tension: 0.3
                    }]
                },
                options: { maintainAspectRatio: false }
            });

            // Gráfico bola
            new Chart(document.getElementById('grafRosca'), {
                type: 'doughnut',
                data: {
                    labels: ['Esc1', 'Esc2', 'Esc3'],
                    datasets: [{
                        data: [d.esc1, d.esc2, d.esc3],
                        backgroundColor: ['#0284c7', '#059669', '#f59e0b']
                    }]
                },
                options: { maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }
            });
        });
});