/* Dashboard charts: risk doughnut, department stacked bars, intervention status.
   Charts render only when their canvas exists, so the same script serves the
   admin, lecturer and advisor dashboards. */

const RISK_COLORS = {
  'Low Risk': '#16a34a',
  'Medium Risk': '#f59e0b',
  'High Risk': '#ef4444',
};

function dashboardData() {
  const el = document.getElementById('dashboard-data');
  if (!el) return { riskCounts: {}, deptDistribution: {}, interventionCounts: {} };
  try {
    return JSON.parse(el.textContent);
  } catch (e) {
    return { riskCounts: {}, deptDistribution: {}, interventionCounts: {} };
  }
}

function renderRiskChart(data) {
  const canvas = document.getElementById('riskChart');
  if (!canvas || typeof Chart === 'undefined') return;
  const labels = ['Low Risk', 'Medium Risk', 'High Risk'];
  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: labels.map((l) => (data.riskCounts && data.riskCounts[l]) || 0),
        backgroundColor: labels.map((l) => RISK_COLORS[l]),
        borderWidth: 2,
        borderColor: '#ffffff',
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, padding: 14 } },
        tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed} students` } },
      },
      cutout: '62%',
    },
  });
}

function renderDeptChart(data) {
  const canvas = document.getElementById('deptChart');
  if (!canvas || typeof Chart === 'undefined') return;
  const dist = data.deptDistribution || {};
  const depts = Object.keys(dist).sort();
  const labels = ['Low Risk', 'Medium Risk', 'High Risk'];
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: depts,
      datasets: labels.map((label) => ({
        label,
        data: depts.map((d) => (dist[d] && dist[d][label]) || 0),
        backgroundColor: RISK_COLORS[label],
        borderRadius: 6,
        borderSkipped: false,
      })),
    },
    options: {
      responsive: true,
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } },
      },
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } } },
    },
  });
}

function renderInterventionChart(data) {
  const canvas = document.getElementById('interventionChart');
  if (!canvas || typeof Chart === 'undefined') return;
  const counts = data.interventionCounts || {};
  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Planned', 'In progress', 'Completed'],
      datasets: [{
        data: [counts.planned || 0, counts.in_progress || 0, counts.completed || 0],
        backgroundColor: ['#94a3b8', '#4f66f6', '#16a34a'],
        borderWidth: 2,
        borderColor: '#ffffff',
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, padding: 14 } },
        tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed}` } },
      },
      cutout: '62%',
    },
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const data = dashboardData();
  renderRiskChart(data);
  renderDeptChart(data);
  renderInterventionChart(data);
});
