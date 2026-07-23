import { featureLabel } from './utils.js';

const chartRegistry = new Map();
const palette = ['#1d4ed8', '#0f766e', '#7c3aed', '#d97706', '#be123c', '#0891b2'];

function replaceChart(canvasId, configuration) {
  const existing = chartRegistry.get(canvasId);
  if (existing) existing.destroy();
  const chart = new Chart(document.getElementById(canvasId), configuration);
  chartRegistry.set(canvasId, chart);
  return chart;
}

function sortedEntries(counts, limit = null) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return limit ? entries.slice(0, limit) : entries;
}

export function renderTypeChart(counts) {
  const entries = sortedEntries(counts);
  replaceChart('typeChart', {
    type: 'bar',
    data: { labels: entries.map(([label]) => label), datasets: [{ label: 'Ocorrências', data: entries.map(([, value]) => value), backgroundColor: palette, borderRadius: 8 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
  });
}

export function renderStatusChart(counts) {
  const entries = sortedEntries(counts);
  replaceChart('statusChart', {
    type: 'doughnut',
    data: { labels: entries.map(([label]) => label), datasets: [{ data: entries.map(([, value]) => value), backgroundColor: palette, borderWidth: 0 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'bottom' } } },
  });
}

export function renderCityChart(counts) {
  const entries = sortedEntries(counts, 8);
  replaceChart('cityChart', {
    type: 'bar',
    data: { labels: entries.map(([label]) => label), datasets: [{ label: 'Ocorrências', data: entries.map(([, value]) => value), backgroundColor: '#0f766e', borderRadius: 8 }] },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } },
  });
}

export function renderFeaturesChart(payload) {
  const entries = payload.features
    .map((feature, index) => [featureLabel(feature), payload.importances[index] * 100])
    .sort((a, b) => b[1] - a[1]);
  replaceChart('featuresChart', {
    type: 'bar',
    data: { labels: entries.map(([label]) => label), datasets: [{ label: 'Importância (%)', data: entries.map(([, value]) => Number(value.toFixed(2))), backgroundColor: '#7c3aed', borderRadius: 8 }] },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { callback: (value) => `${value}%` } } } },
  });
}

export function renderMetricsChart(rows) {
  replaceChart('metricsChart', {
    type: 'bar',
    data: {
      labels: rows.map((row) => row.label),
      datasets: [
        { label: 'Precisão', data: rows.map((row) => row.precision * 100), backgroundColor: '#1d4ed8', borderRadius: 6 },
        { label: 'Cobertura', data: rows.map((row) => row.recall * 100), backgroundColor: '#0f766e', borderRadius: 6 },
        { label: 'F1-score', data: rows.map((row) => row.f1 * 100), backgroundColor: '#d97706', borderRadius: 6 },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { min: 0, max: 100, ticks: { callback: (value) => `${value}%` } } } },
  });
}

export function renderConfusionMatrix(container, matrix, labels) {
  container.replaceChildren();
  if (!Array.isArray(matrix) || !matrix.length) {
    container.textContent = 'Matriz indisponível.';
    return;
  }
  const table = document.createElement('table');
  const head = document.createElement('thead');
  const headRow = document.createElement('tr');
  headRow.appendChild(document.createElement('th'));
  labels.forEach((label) => {
    const th = document.createElement('th');
    th.textContent = label;
    headRow.appendChild(th);
  });
  head.appendChild(headRow);
  table.appendChild(head);
  const body = document.createElement('tbody');
  matrix.forEach((row, rowIndex) => {
    const tr = document.createElement('tr');
    const labelCell = document.createElement('th');
    labelCell.textContent = labels[rowIndex] || `Classe ${rowIndex + 1}`;
    tr.appendChild(labelCell);
    row.forEach((value) => {
      const td = document.createElement('td');
      td.textContent = value;
      tr.appendChild(td);
    });
    body.appendChild(tr);
  });
  table.appendChild(body);
  container.appendChild(table);
}
