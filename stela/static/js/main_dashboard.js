// Define Nord palette
const nord = {
  nord0: '#2e3440',
  nord1: '#3b4252',
  nord2: '#4c566a', // your requested background
  nord3: '#ebcb8b', // line color
  nord4: '#d8dee9',
  white: '#ffffff'
};

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




document.addEventListener('DOMContentLoaded', function() {
    const companiesButton = document.getElementById('btn-companies');
    const popup = document.getElementById('empresas-popup');

    // 1. Toggle the pop-up when the "Empresas" button is clicked
    companiesButton.addEventListener('click', function(event) {
        // Prevent the default link/button action (though not strictly necessary for this button)
        event.preventDefault();

        // Toggle the 'd-none' class to show/hide the pop-up
        popup.classList.toggle('d-none');

        // Stop the click event from propagating to the document body immediately
        event.stopPropagation();

        // Add a listener to close the pop-up when clicking outside
        if (!popup.classList.contains('d-none')) {
            document.addEventListener('click', closePopupOutside);
        } else {
            document.removeEventListener('click', closePopupOutside);
        }
    });

    // 2. Function to close the pop-up when clicking anywhere else on the document
    function closePopupOutside(event) {
        // Check if the click was NOT on the companies button AND NOT inside the pop-up itself
        if (!companiesButton.contains(event.target) && !popup.contains(event.target)) {
            popup.classList.add('d-none');
            // Remove the listener once it's closed to avoid unnecessary overhead
            document.removeEventListener('click', closePopupOutside);
        }
    }

    // 3. Optional: Prevent clicks inside the popup from closing it immediately
    popup.addEventListener('click', function(event) {
        event.stopPropagation();
    });
});