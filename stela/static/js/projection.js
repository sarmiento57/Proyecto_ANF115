document.addEventListener('DOMContentLoaded', function () {
  // seleccionar empresa
  const select = document.getElementById('empresa-select');
  if (select) {
    select.addEventListener('change', function () {
      const empresa = this.value;
      if (empresa) {
        window.location.href = `/stela/projections/?empresa=${empresa}`;
      }
    });
  }

  // etiquetas de los meses
  const labels = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
  ];

  // función segura para extraer datos JSON embebidos
  const parseData = (id) => {
    const el = document.getElementById(id);
    if (!el) return [];
    try {
      return JSON.parse(el.textContent).map(p => p.valor_proyectado);
    } catch (e) {
      console.error(`Error al procesar ${id}:`, e);
      return [];
    }
  };

  const dataMinimos = parseData("dataMinimos");
  const dataPorcentual = parseData("dataPorcentual");
  const dataAbsoluto = parseData("dataAbsoluto");

  const createChart = (ctxId, label, data, color) => {
    const ctx = document.getElementById(ctxId);
    if (!ctx || data.length === 0) return;
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels.slice(0, data.length),
        datasets: [{
          label: label,
          data: data,
          borderColor: color,
          backgroundColor: 'transparent',
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            ticks: {
              color: '#eceff4',
              callback: value => '$' + value.toLocaleString()
            },
            grid: { color: '#4c566a' }
          },
          x: {
            ticks: { color: '#eceff4' },
            grid: { display: false }
          }
        }
      }
    });
  };

  createChart("chartMinimos", "Mínimos Cuadrados", dataMinimos, "#88c0d0");
  createChart("chartPorcentual", "Porcentual", dataPorcentual, "#a3be8c");
  createChart("chartAbsoluto", "Incremento Absoluto", dataAbsoluto, "#ebcb8b");
});
