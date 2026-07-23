import { featureLabel, formatNumber } from './utils.js';

const chartRegistry = new Map();
const palette = ['#1d4ed8', '#0f766e', '#7c3aed', '#d97706', '#be123c', '#0891b2'];

function destroyChart(canvasId) {
  const existing = chartRegistry.get(canvasId);
  if (existing) {
    existing.destroy();
    chartRegistry.delete(canvasId);
  }
}

function setChartAvailability(canvasId, hasData, message = 'Nenhum registro encontrado para os filtros selecionados.') {
  const canvas = document.getElementById(canvasId);
  const container = canvas.parentElement;
  const existingEmptyState = container.querySelector('.chart-empty-state');
  if (hasData) {
    canvas.hidden = false;
    existingEmptyState?.remove();
    return true;
  }
  destroyChart(canvasId);
  canvas.hidden = true;
  if (!existingEmptyState) {
    const emptyState = document.createElement('p');
    emptyState.className = 'chart-empty-state';
    emptyState.textContent = message;
    container.appendChild(emptyState);
  }
  return false;
}

function renderAccessibleTable(canvasId, headers, rows, summary) {
  const summaryElement = document.getElementById(`${canvasId}Summary`);
  const dataContainer = document.getElementById(`${canvasId}Data`);
  if (summaryElement) summaryElement.textContent = summary;
  if (!dataContainer) return;
  dataContainer.replaceChildren();
  if (!rows.length) {
    const empty = document.createElement('p');
    empty.className = 'muted';
    empty.textContent = 'Nenhum dado disponível para esta visualização.';
    dataContainer.appendChild(empty);
    return;
  }
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const headRow = document.createElement('tr');
  headers.forEach((header) => {
    const th = document.createElement('th');
    th.scope = 'col';
    th.textContent = header;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);
  const tbody = document.createElement('tbody');
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    row.forEach((value) => {
      const td = document.createElement('td');
      td.textContent = value;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  dataContainer.appendChild(table);
}

function replaceChart(canvasId, configuration) {
  destroyChart(canvasId);
  const chart = new Chart(document.getElementById(canvasId), configuration);
  chartRegistry.set(canvasId, chart);
  return chart;
}

function sortedEntries(counts, limit = null) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return limit ? entries.slice(0, limit) : entries;
}

function countSummary(entries, subject) {
  if (!entries.length) return `Nenhum dado disponível para ${subject}.`;
  const total = entries.reduce((sum, [, value]) => sum + Number(value || 0), 0);
  const [topLabel, topValue] = entries[0];
  return `${formatNumber(total)} registros distribuídos em ${formatNumber(entries.length)} categoria(s). Maior valor: ${topLabel}, com ${formatNumber(topValue)} registro(s).`;
}

export function renderTypeChart(counts) {
  const entries = sortedEntries(counts);
  renderAccessibleTable('typeChart', ['Tipo', 'Ocorrências'], entries.map(([label, value]) => [label, formatNumber(value)]), countSummary(entries, 'os tipos de ocorrência'));
  if (!setChartAvailability('typeChart', entries.length > 0)) return;
  replaceChart('typeChart', {
    type: 'bar',
    data: { labels: entries.map(([label]) => label), datasets: [{ label: 'Ocorrências', data: entries.map(([, value]) => value), backgroundColor: palette, borderRadius: 8 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
  });
}

export function renderStatusChart(counts) {
  const entries = sortedEntries(counts);
  const total = entries.reduce((sum, [, value]) => sum + Number(value || 0), 0);
  renderAccessibleTable(
    'statusChart',
    ['Status', 'Ocorrências', 'Participação'],
    entries.map(([label, value]) => [label, formatNumber(value), total ? `${((value / total) * 100).toFixed(1)}%` : '0%']),
    countSummary(entries, 'os status dos casos'),
  );
  if (!setChartAvailability('statusChart', entries.length > 0)) return;
  replaceChart('statusChart', {
    type: 'doughnut',
    data: { labels: entries.map(([label]) => label), datasets: [{ data: entries.map(([, value]) => value), backgroundColor: palette, borderWidth: 0 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'bottom' } } },
  });
}

export function renderCityChart(counts) {
  const entries = sortedEntries(counts, 8);
  renderAccessibleTable('cityChart', ['Cidade', 'Ocorrências'], entries.map(([label, value]) => [label, formatNumber(value)]), countSummary(entries, 'as cidades'));
  if (!setChartAvailability('cityChart', entries.length > 0)) return;
  replaceChart('cityChart', {
    type: 'bar',
    data: { labels: entries.map(([label]) => label), datasets: [{ label: 'Ocorrências', data: entries.map(([, value]) => value), backgroundColor: '#0f766e', borderRadius: 8 }] },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } },
  });
}

export function renderFeaturesChart(payload) {
  const features = Array.isArray(payload?.features) ? payload.features : [];
  const importances = Array.isArray(payload?.importances) ? payload.importances : [];
  const entries = features
    .map((feature, index) => [featureLabel(feature), Number(importances[index] || 0) * 100])
    .sort((a, b) => b[1] - a[1]);
  const summary = entries.length
    ? `${entries.length} variáveis avaliadas. A mais relevante é ${entries[0][0]}, com ${entries[0][1].toFixed(2)}% de importância.`
    : 'Importância das variáveis indisponível.';
  renderAccessibleTable('featuresChart', ['Variável', 'Importância'], entries.map(([label, value]) => [label, `${value.toFixed(2)}%`]), summary);
  if (!setChartAvailability('featuresChart', entries.length > 0, 'A importância das variáveis não está disponível.')) return;
  replaceChart('featuresChart', {
    type: 'bar',
    data: { labels: entries.map(([label]) => label), datasets: [{ label: 'Importância (%)', data: entries.map(([, value]) => Number(value.toFixed(2))), backgroundColor: '#7c3aed', borderRadius: 8 }] },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { callback: (value) => `${value}%` } } } },
  });
}

export function renderMetricsChart(rows) {
  const validRows = Array.isArray(rows) ? rows : [];
  const summary = validRows.length
    ? `Métricas de precisão, cobertura e F1-score para ${validRows.length} classe(s).`
    : 'Métricas por classe indisponíveis.';
  renderAccessibleTable(
    'metricsChart',
    ['Classe', 'Precisão', 'Cobertura', 'F1-score'],
    validRows.map((row) => [row.label, `${(row.precision * 100).toFixed(1)}%`, `${(row.recall * 100).toFixed(1)}%`, `${(row.f1 * 100).toFixed(1)}%`]),
    summary,
  );
  if (!setChartAvailability('metricsChart', validRows.length > 0, 'As métricas por classe não estão disponíveis.')) return;
  replaceChart('metricsChart', {
    type: 'bar',
    data: {
      labels: validRows.map((row) => row.label),
      datasets: [
        { label: 'Precisão', data: validRows.map((row) => row.precision * 100), backgroundColor: '#1d4ed8', borderRadius: 6 },
        { label: 'Cobertura', data: validRows.map((row) => row.recall * 100), backgroundColor: '#0f766e', borderRadius: 6 },
        { label: 'F1-score', data: validRows.map((row) => row.f1 * 100), backgroundColor: '#d97706', borderRadius: 6 },
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
  table.setAttribute('aria-label', 'Matriz de confusão do modelo');
  const head = document.createElement('thead');
  const headRow = document.createElement('tr');
  const corner = document.createElement('th');
  corner.scope = 'col';
  corner.textContent = 'Real / Prevista';
  headRow.appendChild(corner);
  labels.forEach((label) => {
    const th = document.createElement('th');
    th.scope = 'col';
    th.textContent = label;
    headRow.appendChild(th);
  });
  head.appendChild(headRow);
  table.appendChild(head);
  const body = document.createElement('tbody');
  matrix.forEach((row, rowIndex) => {
    const tr = document.createElement('tr');
    const labelCell = document.createElement('th');
    labelCell.scope = 'row';
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
