/* --- Paleta de Colores Nord --- */
const nord = {
  nord0: '#2e3440',
  nord1: '#3b4252',
  nord2: '#4c566a', // Fondo del gráfico
  nord3: '#ebcb8b', // Amarillo
  nord4: '#d8dee9',
  white: '#ffffff',
  nord8: '#88c0d0', // Azul claro
  nord9: '#d08770', // Naranja
  nord10: '#a3be8c', // Verde
  nord11: '#bf616a', // Rojo (para "NO DATA")
  nord12: '#5e81ac', // Azul oscuro
  nord13: '#b48ead', // Púrpura
};

// Colores para las líneas del gráfico múltiple
const chartColors = [nord.nord3, nord.nord8, nord.nord9, nord.nord10, nord.nord12, nord.nord13];

/* --- Plugin de Fondo --- */
const backgroundPlugin = {
  id: 'customBackgroundColor',
  beforeDraw(chart) {
    const { ctx, chartArea } = chart;
    ctx.save();
    ctx.fillStyle = nord.nord2;
    ctx.fillRect(chartArea.left, chartArea.top, chartArea.width, chartArea.height);
    ctx.restore();
  }
};

/* --- Plugin "NO DATA" --- */
const noDataPlugin = {
  id: 'noDataPlugin',
  afterDraw(chart) {
    // Si no hay datasets, o si todos los datasets están vacíos
    if (chart.data.datasets.length === 0 || chart.data.datasets.every(d => d.data.length === 0)) {
      const { ctx, width, height } = chart;
      ctx.save();
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = "bold 20px 'Lato', sans-serif";
      ctx.fillStyle = nord.nord11; // Rojo Nord
      ctx.fillText('NO DATA', width / 2, height / 2);
      ctx.restore();
    }
  }
};

/* --- Generador de Gráficos --- */
function makeChart(ctx, chartType) {
  const chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [] // Inicia vacío para que actúe el plugin "NO DATA"
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true },
      },
      scales: {
        x: { ticks: { color: nord.white }, grid: { color: nord.white, lineWidth: 0.2 } },
        y: { ticks: { color: nord.white }, grid: { color: nord.white, lineWidth: 0.2 } }
      },
      onClick: (event, elements, chart) => {
        handleChartClick(chart, chartType);
      }
    },
    plugins: [backgroundPlugin, noDataPlugin]
  });
  return chartInstance;
}

// --- Variables globales para los gráficos y el modal ---
let chart1, chart2, chart3;
let chartModalInstance = null;
let modalTitleEl = null;
let modalBodyEl = null;
let modalFooterEl = null;

/* --- Cargar datos reales en un gráfico --- */
async function loadChartData(chartInstance, type, itemIds = []) {
  chartInstance.data.labels = [];
  chartInstance.data.datasets = [];

  if (itemIds.length === 0) {
    chartInstance.update(); // Actualiza para mostrar "NO DATA"
    return;
  }

  try {
    const params = new URLSearchParams();
    params.append('type', type);
    itemIds.forEach(id => params.append('ids', id));

    const response = await fetch(`/api/get-chart-data/?${params.toString()}`);

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Error del servidor');
    }

    const data = await response.json(); // Espera { labels: [...], datasets: [...] }

    // Aplicar colores y estilo
    data.datasets.forEach((dataset, index) => {
      dataset.borderColor = chartColors[index % chartColors.length];
      dataset.tension = 0.3;
      dataset.borderWidth = 2;
      dataset.pointRadius = 0;
      dataset.fill = false;
    });

    chartInstance.data.labels = data.labels;
    chartInstance.data.datasets = data.datasets;
    chartInstance.update();

  } catch (error) {
    console.error("Error cargando datos del gráfico:", error);
    chartInstance.update(); // Limpia el gráfico, mostrará "NO DATA"
  }
}

/* --- Lógica para el modal de selección MÚLTIPLE --- */
async function showMultiSelectForm(chart, type, apiUrl) {
  modalTitleEl.textContent = `Seleccionar ${type === 'cuentas' ? 'Cuentas' : 'Ratios'}`;
  modalBodyEl.innerHTML = '<p>Cargando...</p>';
  modalFooterEl.innerHTML = '';

  try {
    const response = await fetch(apiUrl);
    const data = await response.json();

    if (data.length === 0) {
      modalBodyEl.innerHTML = '<p>No se encontraron opciones (¿Has cargado un catálogo?).</p>';
      return;
    }

    let checkboxesHTML = data.map(item => {
      const id = item.clave || item.id;
      const name = item.codigo ? `${item.codigo} - ${item.nombre}` : item.nombre;
      return `
        <div class="form-check">
          <input class="form-check-input" type="checkbox" value="${id}" id="chk-${id}">
          <label class="form-check-label" for="chk-${id}">
            ${name}
          </label>
        </div>`;
    }).join('');
    modalBodyEl.innerHTML = `<div class="list-container" style="max-height: 300px; overflow-y: auto;">${checkboxHTML}</div>`;

    modalFooterEl.innerHTML = '<button id="btn-plot-multi" class="btn btn-success">Graficar Seleccionados</button>';

    document.getElementById('btn-plot-multi').onclick = () => {
      const selectedIds = [];
      modalBodyEl.querySelectorAll('input[type="checkbox"]:checked').forEach(chk => {
        selectedIds.push(chk.value);
      });
      chartModalInstance.hide();
      loadChartData(chart, type, selectedIds);
    };

  } catch (error) {
    modalBodyEl.innerHTML = `<p class="text-danger">Error al cargar: ${error.message}</p>`;
  }
}

/* --- Pantalla de inicio para el gráfico 3 (Múltiple) --- */
function showMultiSelectHome(chart) {
  modalTitleEl.textContent = 'Comparación Múltiple';
  modalBodyEl.innerHTML = `
    <p>¿Qué te gustaría comparar?</p>
    <button id="btn-comp-cuentas" class="btn btn-primary w-100 mb-2">
      Comparar Cuentas
    </button>
    <button id="btn-comp-ratios" class="btn btn-primary w-100">
      Comparar Ratios
    </button>
  `;
  modalFooterEl.innerHTML = '';
  chartModalInstance.show();

  document.getElementById('btn-comp-cuentas').onclick = () => {
    showMultiSelectForm(chart, 'cuentas', '/api/get-cuentas/');
  };
  document.getElementById('btn-comp-ratios').onclick = () => {
    showMultiSelectForm(chart, 'ratios', '/api/get-ratios/');
  };
}

/* --- Lógica para el modal de selección SIMPLE (Gráficos 1 y 2) --- */
async function showSingleSelect(chart, type, apiUrl) {
  modalTitleEl.textContent = `Seleccionar ${type === 'cuentas' ? 'Cuenta' : 'Ratio'}`;
  modalBodyEl.innerHTML = '<p>Cargando...</p>';
  modalFooterEl.innerHTML = '';
  chartModalInstance.show();

  try {
    const response = await fetch(apiUrl);
    const data = await response.json();

    if (data.length === 0) {
      modalBodyEl.innerHTML = '<p>No se encontraron opciones (¿Has cargado un catálogo?).</p>';
      return;
    }

    const listGroup = document.createElement('div');
    listGroup.className = 'list-group';
    data.forEach(item => {
      const id = item.clave || item.id;
      const name = item.codigo ? `${item.codigo} - ${item.nombre}` : item.nombre;

      const a = document.createElement('a');
      a.href = '#';
      a.className = 'list-group-item list-group-item-action';
      a.textContent = name;
      a.dataset.itemId = id;

      a.onclick = (e) => {
        e.preventDefault();
        chartModalInstance.hide();
        loadChartData(chart, type, [id]); // Cargar datos para UN ID
      };
      listGroup.appendChild(a);
    });
    modalBodyEl.innerHTML = '';
    modalBodyEl.appendChild(listGroup);

  } catch (error) {
    modalBodyEl.innerHTML = `<p class="text-danger">Error al cargar: ${error.message}</p>`;
  }
}

/* --- Manejador de Clic Principal --- */
function handleChartClick(chartInstance, chartType) {
  if (!chartModalInstance) {
    console.error("Modal no inicializado");
    return;
  }

  if (chartType === 'cuentas') {
    showSingleSelect(chartInstance, 'cuentas', '/api/get-cuentas/');
  } else if (chartType === 'ratios') {
    showSingleSelect(chartInstance, 'ratios', '/api/get-ratios/');
  } else if (chartType === 'multi') {
    showMultiSelectHome(chartInstance);
  }
}

/* --- ¡MODIFICADO! DOMContentLoaded --- */
window.addEventListener('DOMContentLoaded', () => {
  // 1. Inicializar referencias del Modal
  const modalEl = document.getElementById('chartOptionsModal');
  if (modalEl) {
    chartModalInstance = new bootstrap.Modal(modalEl);
    modalTitleEl = document.getElementById('chartOptionsModalLabel');
    modalBodyEl = document.getElementById('chartOptionsModalBody');
    modalFooterEl = document.getElementById('chartOptionsModalFooter');
  } else {
    console.error("No se encontró el HTML del modal (#chartOptionsModal).");
  }

  // 2. Crear los 3 gráficos (se inician vacíos)
  // El plugin 'noDataPlugin' mostrará "NO DATA"
  chart1 = makeChart(document.getElementById('chart-x').getContext('2d'), 'cuentas');
  chart2 = makeChart(document.getElementById('chart-x2').getContext('2d'), 'ratios');
  chart3 = makeChart(document.getElementById('chart-x3').getContext('2d'), 'multi');

  // 3. (Se eliminó la carga de datos por defecto)

  // 4. Lógica de la tabla de catálogo (la dejé por si la usas en otra parte)
  const tableBody = document.querySelector('#catalog-table tbody');
  const catalogActions = document.getElementById('catalog-actions');
  const parentCard = catalogActions ? catalogActions.closest('.card') : null;

  if (tableBody && catalogActions && parentCard) {
    const isTableEmpty = tableBody.children.length === 0;
    if (isTableEmpty) {
      catalogActions.classList.add('is-centered');
      parentCard.classList.add('is-empty-catalog');
    } else {
      catalogActions.classList.remove('is-centered');
      parentCard.classList.remove('is-empty-catalog');
    }
  }
});