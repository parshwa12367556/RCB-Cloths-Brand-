/* ARENA CHARTS - Chart.js Revenue Chart + Animated Counters + Period Toggle */
document.addEventListener('DOMContentLoaded', function () {

    /* ANIMATED COUNTERS */
    function animateCounter(element, target, prefix, suffix, decimals, duration) {
        prefix = prefix || '';
        suffix = suffix || '';
        decimals = parseInt(decimals) || 0;
        duration = duration || 1800;
        var startTime = null;

        function easeOutExpo(t) {
            return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
        }

        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            var progress = Math.min((timestamp - startTime) / duration, 1);
            var easedProgress = easeOutExpo(progress);
            var current = target * easedProgress;

            if (decimals > 0) {
                element.textContent = prefix + current.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + suffix;
            } else {
                element.textContent = prefix + Math.floor(current).toLocaleString('en-IN') + suffix;
            }

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        }

        requestAnimationFrame(step);
    }

    var counters = document.querySelectorAll('[data-counter]');
    counters.forEach(function (el, index) {
        var key = el.getAttribute('data-counter');
        var target = counterTargets[key] || 0;
        var prefix = el.getAttribute('data-prefix') || '';
        var suffix = el.getAttribute('data-suffix') || '';
        var decimals = el.getAttribute('data-decimals') || '0';
        setTimeout(function () {
            animateCounter(el, target, prefix, suffix, decimals, 2000);
        }, 300 + (index * 120));
    });

    /* REVENUE AND PROFIT CHART WITH PERIOD TOGGLE */
    var ctx = document.getElementById('revenueChart');
    if (!ctx) return;

    var canvas = ctx.getContext('2d');
    var revenueGradient = canvas.createLinearGradient(0, 0, 0, 300);
    revenueGradient.addColorStop(0, 'rgba(244, 180, 0, 0.35)');
    revenueGradient.addColorStop(0.5, 'rgba(244, 180, 0, 0.10)');
    revenueGradient.addColorStop(1, 'rgba(244, 180, 0, 0.0)');

    var profitGradient = canvas.createLinearGradient(0, 0, 0, 300);
    profitGradient.addColorStop(0, 'rgba(183, 255, 0, 0.30)');
    profitGradient.addColorStop(0.5, 'rgba(183, 255, 0, 0.08)');
    profitGradient.addColorStop(1, 'rgba(183, 255, 0, 0.0)');

    var revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.daily.labels,
            datasets: [
                {
                    label: 'Revenue',
                    data: chartData.daily.revenue,
                    borderColor: '#F4B400',
                    backgroundColor: revenueGradient,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 7,
                    pointBackgroundColor: '#F4B400',
                    pointBorderColor: '#08090B',
                    pointBorderWidth: 2,
                    pointHoverBorderColor: '#F8FAFC',
                    pointHoverBorderWidth: 3
                },
                {
                    label: 'Profit',
                    data: chartData.daily.profit,
                    borderColor: '#B7FF00',
                    backgroundColor: profitGradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#B7FF00',
                    pointBorderColor: '#08090B',
                    pointBorderWidth: 2,
                    pointHoverBorderColor: '#F8FAFC',
                    pointHoverBorderWidth: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 800, easing: 'easeOutQuart' },
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(21, 23, 28, 0.95)',
                    titleColor: '#F8FAFC',
                    bodyColor: '#BFC7D5',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 10,
                    padding: 14,
                    titleFont: { family: "'Montserrat', sans-serif", weight: '700', size: 12 },
                    bodyFont: { family: "'Inter', sans-serif", size: 13 },
                    displayColors: true,
                    boxWidth: 10,
                    boxHeight: 10,
                    boxPadding: 4,
                    usePointStyle: true,
                    callbacks: {
                        label: function(context) {
                            return ' ' + context.dataset.label + ': ' + context.parsed.y.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
                    ticks: { color: '#8A92A0', font: { family: "'Inter', sans-serif", size: 11 }, maxRotation: 0 },
                    border: { display: false }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
                    ticks: {
                        color: '#8A92A0',
                        font: { family: "'Inter', sans-serif", size: 11 },
                        callback: function(value) { return value.toLocaleString('en-IN'); }
                    },
                    border: { display: false },
                    beginAtZero: true
                }
            }
        }
    });

    /* PERIOD TOGGLE HANDLER */
    window.switchChartPeriod = function(period) {
        var data = chartData[period];
        if (!data) return;

        // Update toggle buttons
        document.querySelectorAll('.chart-toggle-btn').forEach(function(btn) {
            btn.classList.remove('active');
            if (btn.getAttribute('data-period') === period) {
                btn.classList.add('active');
            }
        });

        // Update chart data with smooth animation
        revenueChart.data.labels = data.labels;
        revenueChart.data.datasets[0].data = data.revenue;
        revenueChart.data.datasets[1].data = data.profit;
        revenueChart.update('active');
    };
});
