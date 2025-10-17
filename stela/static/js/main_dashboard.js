// Simple client-side state for demo and Django friendliness
const companiesEl = document.getElementById('companies');
const catalogActions = document.getElementById('catalog-actions');
const saveCompanyBtn = document.getElementById('save-company');
const companyNameInput = document.getElementById('company-name');

// initial companies (empty array -> shows catalog actions)
let companies = []; // you can preload companies here, e.g. ['Empresa 1']

function renderCompanies(){
  companiesEl.innerHTML = '';
  companies.forEach((c, i)=>{
    const li = document.createElement('li');
    li.className = 'd-flex justify-content-between align-items-center mb-1';
    li.innerHTML = `<span>${c}</span><button class="btn btn-sm btn-outline-light btn-select" data-index="${i}">Seleccionar</button>`;
    companiesEl.appendChild(li);
  });

  toggleCatalogActions();
}

function toggleCatalogActions(){
  // If there is at least one company, hide the floating actions
  if(companies.length > 0){
    catalogActions.style.display = 'none';
  } else {
    catalogActions.style.display = 'flex';
  }
}

// Hook up saving a company
saveCompanyBtn.addEventListener('click', ()=>{
  const name = companyNameInput.value.trim();
  if(!name) return;
  companies.push(name);
  companyNameInput.value = '';
  // close modal (Bootstrap)
  const modal = bootstrap.Modal.getInstance(document.getElementById('modalCompany'));
  modal.hide();
  renderCompanies();
});

// initial render
renderCompanies();

// Charts (x, x^2, x^3)
function makeData(func){
  const labels = [];
  const data = [];
  for(let x=-5;x<=5;x+=0.5){
    labels.push(x);
    data.push(func(x));
  }
  return {labels, data};
}

function makeChart(ctx, func, label){
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
        pointRadius: 0.5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins:{
        legend:{display:false}
      },
      scales: {
        x: { display: true },
        y: { display: true }
      }
    }
  });
}

// create charts when DOM ready
window.addEventListener('DOMContentLoaded', ()=>{
  makeChart(document.getElementById('chart-x').getContext('2d'), x=>x, 'x');
  makeChart(document.getElementById('chart-x2').getContext('2d'), x=>x*x, 'x^2');
  makeChart(document.getElementById('chart-x3').getContext('2d'), x=>x*x*x, 'x^3');
});