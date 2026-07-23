import { api, ApiError } from './api.js';
import {
  renderCityChart,
  renderConfusionMatrix,
  renderFeaturesChart,
  renderMetricsChart,
  renderStatusChart,
  renderTypeChart,
} from './charts.js';
import {
  renderOccurrencesTable,
  renderTableLoading,
  updateSortIndicators,
} from './table.js';
import {
  countBy,
  downloadCsv,
  fillSelect,
  formatDate,
  formatNumber,
  formatPercent,
  topEntry,
  uniqueSorted,
} from './utils.js';

const state = {
  cases: [], filteredCases: [],
  filters: { busca: '', tipoCrime: '', status: '', cidade: '', uf: '', dataInicial: '', dataFinal: '' },
  table: { page: 1, perPage: 10, sortBy: 'data', order: 'desc' },
  model: { evaluation: null, classes: {}, features: null },
};

const elements = {
  loading: document.getElementById('loadingOverlay'),
  globalError: document.getElementById('globalError'),
  globalErrorMessage: document.getElementById('globalErrorMessage'),
  apiStatus: document.getElementById('apiStatus'),
  modelAvailability: document.getElementById('modelAvailability'),
  filtersForm: document.getElementById('filtersForm'),
  predictionForm: document.getElementById('predictionForm'),
  predictionResult: document.getElementById('predictionResult'),
};

function setLoading(isLoading) { elements.loading.hidden = !isLoading; }

function setApiStatus(mode, text) {
  elements.apiStatus.className = `status-badge status-badge--${mode}`;
  elements.apiStatus.innerHTML = '<span class="status-dot" aria-hidden="true"></span>';
  elements.apiStatus.append(document.createTextNode(text));
}

function setGlobalError(message = '') {
  elements.globalError.hidden = !message;
  elements.globalErrorMessage.textContent = message;
}

function readFilters() {
  const formData = new FormData(elements.filtersForm);
  return Object.fromEntries(Object.keys(state.filters).map((key) => [key, String(formData.get(key) || '').trim()]));
}

function applyLocalFilters() {
  const filters = state.filters;
  const search = filters.busca.toLocaleLowerCase('pt-BR');
  state.filteredCases = state.cases.filter((item) => {
    if (filters.tipoCrime && item.tipoCrime !== filters.tipoCrime) return false;
    if (filters.status && item.status !== filters.status) return false;
    if (filters.cidade && item.cidade !== filters.cidade) return false;
    if (filters.uf && item.uf !== filters.uf) return false;
    if (filters.dataInicial && (!item.data || item.data < filters.dataInicial)) return false;
    if (filters.dataFinal && (!item.data || item.data > filters.dataFinal)) return false;
    if (search) {
      const searchable = [item.id, item.tipoCrime, item.status, item.cidade, item.uf, item.descricao, item.perito]
        .join(' ').toLocaleLowerCase('pt-BR');
      if (!searchable.includes(search)) return false;
    }
    return true;
  });
}

function setKpi(id, value, hint = '') {
  document.getElementById(id).textContent = value;
  const hintElement = document.getElementById(`${id}Hint`);
  if (hintElement) hintElement.textContent = hint;
}

function renderKpis() {
  const items = state.filteredCases;
  const statusCounts = countBy(items, 'status');
  const typeCounts = countBy(items, 'tipoCrime');
  const cityCounts = countBy(items, 'cidade');
  const [topType, topTypeCount] = topEntry(typeCounts);
  const [topCity, topCityCount] = topEntry(cityCounts);
  const total = items.length;
  const investigation = statusCounts['Em investigação'] || 0;
  const completed = statusCounts.Concluído || 0;
  setKpi('kpiTotal', formatNumber(total), total === state.cases.length ? 'Base completa' : 'Após os filtros');
  setKpi('kpiInvestigacao', formatNumber(investigation), total ? `${((investigation / total) * 100).toFixed(1)}% do conjunto` : 'Sem registros');
  setKpi('kpiConcluidas', formatNumber(completed), total ? `${((completed / total) * 100).toFixed(1)}% do conjunto` : 'Sem registros');
  setKpi('kpiTipo', topType, topTypeCount ? `${formatNumber(topTypeCount)} ocorrência(s)` : 'Sem registros');
  setKpi('kpiCidade', topCity, topCityCount ? `${formatNumber(topCityCount)} ocorrência(s)` : 'Sem registros');
}

function renderDataCharts() {
  renderTypeChart(countBy(state.filteredCases, 'tipoCrime'));
  renderStatusChart(countBy(state.filteredCases, 'status'));
  renderCityChart(countBy(state.filteredCases, 'cidade'));
}

function populateFiltersAndPrediction() {
  const types = uniqueSorted(state.cases, 'tipoCrime');
  const statuses = uniqueSorted(state.cases, 'status');
  const cities = uniqueSorted(state.cases, 'cidade');
  const ufs = uniqueSorted(state.cases, 'uf');
  fillSelect(document.getElementById('filterType'), types, 'Todos');
  fillSelect(document.getElementById('filterStatus'), statuses, 'Todos');
  fillSelect(document.getElementById('filterCity'), cities, 'Todas');
  fillSelect(document.getElementById('filterUf'), ufs, 'Todas');
  fillSelect(document.getElementById('predictionType'), types);
  fillSelect(document.getElementById('predictionCity'), cities);
  fillSelect(document.getElementById('predictionUf'), ufs);

  const cityUfMap = new Map(state.cases.map((item) => [item.cidade, item.uf]));
  const citySelect = document.getElementById('predictionCity');
  const ufSelect = document.getElementById('predictionUf');
  const syncUf = () => {
    const uf = cityUfMap.get(citySelect.value);
    if (uf) ufSelect.value = uf;
  };
  citySelect.addEventListener('change', syncUf);
  syncUf();
  const dates = state.cases.map((item) => item.data).filter(Boolean).sort();
  document.getElementById('predictionDate').value = dates.at(-1) || new Date().toISOString().slice(0, 10);
  document.getElementById('predictionTime').value = '18:30';
}

async function loadTable() {
  renderTableLoading();
  try {
    const payload = await api.paginatedCases({
      pagina: state.table.page,
      porPagina: state.table.perPage,
      ordenarPor: state.table.sortBy,
      ordem: state.table.order,
      ...state.filters,
    });
    renderOccurrencesTable(payload.items, payload.pagination);
    updateSortIndicators(payload.sorting.field, payload.sorting.order);
  } catch (error) {
    const message = error instanceof ApiError ? error.message : 'Falha ao carregar a tabela.';
    const body = document.getElementById('occurrencesTableBody');
    body.replaceChildren();
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 7;
    cell.className = 'empty-state';
    cell.textContent = message;
    row.appendChild(cell);
    body.appendChild(row);
    document.getElementById('tableSummary').textContent = 'Tabela temporariamente indisponível.';
  }
}

async function applyFilters({ resetPage = true } = {}) {
  state.filters = readFilters();
  if (resetPage) state.table.page = 1;
  applyLocalFilters();
  renderKpis();
  renderDataCharts();
  await loadTable();
}

function modelRows(evaluation, classes) {
  return Object.entries(evaluation)
    .filter(([key, value]) => /^\d+$/.test(key) && value && typeof value === 'object')
    .map(([key, value]) => ({
      key, label: classes[key] || `Classe ${key}`,
      precision: Number(value.precision || 0), recall: Number(value.recall || 0),
      f1: Number(value['f1-score'] || 0), support: Number(value.support || 0),
    }));
}

function renderMetricsTable(rows) {
  const body = document.getElementById('metricsTableBody');
  body.replaceChildren();
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    [row.label, formatPercent(row.precision), formatPercent(row.recall), formatPercent(row.f1), formatNumber(row.support)]
      .forEach((value) => {
        const td = document.createElement('td');
        td.textContent = value;
        tr.appendChild(td);
      });
    body.appendChild(tr);
  });
}

function renderModel() {
  const { evaluation, classes, features } = state.model;
  if (!evaluation || !features) {
    elements.modelAvailability.className = 'status-badge status-badge--danger';
    elements.modelAvailability.textContent = 'Modelo indisponível';
    return;
  }
  const rows = modelRows(evaluation, classes);
  const metadata = evaluation.metadata || {};
  elements.modelAvailability.className = 'status-badge status-badge--success';
  elements.modelAvailability.textContent = 'Modelo disponível';
  document.getElementById('metricAccuracy').textContent = formatPercent(evaluation.accuracy || 0, 1);
  document.getElementById('metricSamples').textContent = formatNumber(metadata.amostras || 0);
  document.getElementById('metricClasses').textContent = formatNumber(rows.length);
  document.getElementById('metricReferenceDate').textContent = formatDate(metadata.data_referencia);
  renderFeaturesChart(features);
  renderMetricsChart(rows);
  renderMetricsTable(rows);
  renderConfusionMatrix(document.getElementById('confusionMatrix'), evaluation.confusion_matrix, rows.map((row) => row.label));
}

async function loadModelData() {
  const [featuresResult, evaluationResult, classesResult] = await Promise.allSettled([
    api.features(), api.evaluation(), api.classes(),
  ]);
  if (featuresResult.status === 'fulfilled') state.model.features = featuresResult.value;
  if (evaluationResult.status === 'fulfilled') state.model.evaluation = evaluationResult.value;
  if (classesResult.status === 'fulfilled') state.model.classes = classesResult.value;
  renderModel();
}

async function loadDashboard() {
  setLoading(true);
  setGlobalError('');
  setApiStatus('loading', 'Verificando API');
  try {
    const [status, cases] = await Promise.all([api.status(), api.cases()]);
    if (!Array.isArray(cases)) throw new ApiError('A API retornou um formato de dados inesperado.');
    state.cases = cases;
    populateFiltersAndPrediction();
    state.filters = readFilters();
    applyLocalFilters();
    renderKpis();
    renderDataCharts();
    await Promise.all([loadTable(), loadModelData()]);
    setApiStatus('success', status.modelo_disponivel ? 'API e modelo online' : 'API online');
  } catch (error) {
    const message = error instanceof ApiError ? error.message : 'Erro inesperado ao iniciar o dashboard.';
    setGlobalError(message);
    setApiStatus('danger', 'API indisponível');
  } finally {
    setLoading(false);
  }
}

async function handlePrediction(event) {
  event.preventDefault();
  const button = document.getElementById('predictionButton');
  const result = elements.predictionResult;
  button.disabled = true;
  button.textContent = 'Processando...';
  result.hidden = false;
  result.textContent = 'Executando o pipeline de classificação...';
  try {
    const payload = await api.predict({
      tipoCrime: document.getElementById('predictionType').value,
      cidade: document.getElementById('predictionCity').value,
      uf: document.getElementById('predictionUf').value,
      data: document.getElementById('predictionDate').value,
      hora: document.getElementById('predictionTime').value,
    });
    result.replaceChildren();
    const title = document.createElement('strong');
    title.textContent = `Status estimado: ${payload.previsao_status}`;
    const detail = document.createElement('span');
    detail.textContent = `Confiança do modelo: ${formatPercent(payload.confianca, 1)}. ${payload.aviso}`;
    result.append(title, detail);
  } catch (error) {
    result.textContent = error instanceof ApiError ? error.message : 'Não foi possível executar a simulação.';
  } finally {
    button.disabled = false;
    button.textContent = 'Executar simulação';
  }
}

function bindEvents() {
  elements.filtersForm.addEventListener('submit', (event) => { event.preventDefault(); applyFilters(); });
  document.getElementById('clearFiltersButton').addEventListener('click', () => { elements.filtersForm.reset(); applyFilters(); });
  document.getElementById('exportButton').addEventListener('click', () => {
    try { downloadCsv(state.filteredCases); } catch (error) { window.alert(error.message); }
  });
  document.getElementById('pageSize').addEventListener('change', (event) => {
    state.table.perPage = Number(event.target.value); state.table.page = 1; loadTable();
  });
  document.getElementById('previousPage').addEventListener('click', () => { state.table.page = Math.max(1, state.table.page - 1); loadTable(); });
  document.getElementById('nextPage').addEventListener('click', () => { state.table.page += 1; loadTable(); });
  document.querySelectorAll('.sort-button').forEach((button) => {
    button.addEventListener('click', () => {
      const field = button.dataset.sort;
      if (state.table.sortBy === field) state.table.order = state.table.order === 'asc' ? 'desc' : 'asc';
      else { state.table.sortBy = field; state.table.order = 'asc'; }
      state.table.page = 1;
      loadTable();
    });
  });
  elements.predictionForm.addEventListener('submit', handlePrediction);
  document.getElementById('retryButton').addEventListener('click', loadDashboard);
}

bindEvents();
loadDashboard();
