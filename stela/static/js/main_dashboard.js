// Utility to generate data
function makeData(func) {
  const labels = [];
  const data = [];
  for (let x = -5; x <= 5; x += 0.5) {
    labels.push(x);
    data.push(func(x));
  }
  return { labels, data };
}

// Custom background plugin for Chart.js
const backgroundPlugin = {
  id: 'customBackgroundColor',
  beforeDraw(chart) {
    const { ctx, chartArea } = chart;
    ctx.save();
    ctx.fillStyle = nord.nord2; // background color for chart
    ctx.fillRect(chartArea.left, chartArea.top, chartArea.width, chartArea.height);
    ctx.restore();
  }
};

// Chart generator
function makeChart(ctx, func, label) {
  const d = makeData(func);
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: d.labels,
      datasets: [{
        label: label,
        data: d.data,
        tension: 0.3,
        fill: false,
        borderWidth: 2,
        borderColor: nord.nord3, // line color
        pointRadius: 0,          // hide points
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          ticks: { color: nord.white },
          grid: { color: nord.white, lineWidth: 0.2 },
        },
        y: {
          ticks: { color: nord.white },
          grid: { color: nord.white, lineWidth: 0.2 },
        }
      }
    },
    plugins: [backgroundPlugin]
  });
}

// Create charts when DOM ready
window.addEventListener('DOMContentLoaded', () => {
  makeChart(document.getElementById('chart-x').getContext('2d'), x => x, 'x');
  makeChart(document.getElementById('chart-x2').getContext('2d'), x => x * x, 'x²');
  makeChart(document.getElementById('chart-x3').getContext('2d'), x => x * x * x, 'x³');
});




