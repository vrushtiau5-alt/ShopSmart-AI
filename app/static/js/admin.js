/**
 * ShopSmart AI - Admin Executive Dashboard Charts
 */
document.addEventListener('DOMContentLoaded', function () {
    const catCanvas = document.getElementById('categoryChart');
    const statusCanvas = document.getElementById('statusChart');

    if (catCanvas && window.categoryChartLabels) {
        new Chart(catCanvas, {
            type: 'doughnut',
            data: {
                labels: window.categoryChartLabels,
                datasets: [{
                    data: window.categoryChartData,
                    backgroundColor: ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#64748b']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    if (statusCanvas && window.statusChartLabels) {
        new Chart(statusCanvas, {
            type: 'bar',
            data: {
                labels: window.statusChartLabels,
                datasets: [{
                    label: 'Orders Count',
                    data: window.statusChartData,
                    backgroundColor: '#6366f1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } }
                }
            }
        });
    }
});
