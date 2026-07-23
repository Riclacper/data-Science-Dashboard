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

const defaultFilters = {
  busca: '', tipoCrime: '', status: '', cidade: '', uf: '', dataInicial: '', dataFinal: '',
};
const allowedSortFields = ['id', 'tipoCrime', 'status', 'data', 'hora', 'cidade', 'perito'];
const filterLabels = {
  busca: 'Busca', tipoCrime: 'Tipo', status: 'Status', cidade: 'Cidade', uf: 'UF',
  dataInicial: 'A partir de', dataFinal: 'Até',
};
const state = {
  cases: [], filteredCases: [],
  filters: { ...defaultFilters },
  table: { page: 1, perPage: 10, sortBy: 'data', order: 'desc' },
  model: { evaluation: null, classes: {}, features: null },
};

const elements = {
  main: document.getElementById('conteudo-principal'),
  loadingStatus: document.getElementById('loadingStatus'),
  globalError: document.getElementById('globalError'),
  globalErrorMessage: document.getElementById('globalErrorMessage'),
  apiStatus: document.getElementById('apiStatus'),
  modelAvailability: document.getElementById('modelAvailability'),
  filtersForm: document.getElementById('filtersForm'),
  activeFilters: document.getElementById('activeFilters'),
  predictionForm: document.getElementById('predictionForm'),
  predictionResult: document.getElementById('predictionResult'),
  toastRegion: document.getElementById('toastRegion'),
};

let searchTimer;
let tableRequestSequence = 0;

function setLoading(isLoading) {
  document.body.classList.toggle('is-loading', isLoading);
  elements.main.setAttribute('aria-busy', String(isLoading));
  elements.loadingStatus.hidden = !isLoading;
}

function setApiStatus(mode, text) {
  elements.apiStatus.className = `status-badge status-badge--${mode}`;
  elements.apiStatus.innerHTML = '<span class="status-dot" aria-hidden="true"></span>';
  elements.apiStatus.append(document.createTextNode(text));
}

function setGlobalError(message = '') {
  elements.globalError.hidden = !message;
  elements.globalErrorMessage.textContent = message;
}

function showToast(message, tone = 'success', title = null) {
  const toast = document.createElement('article');
  toast.className = `toast toast--${tone}`;
  toast.setAttribute('role', tone === 'danger' ? 'alert' : 'status');
  const content = document.createElement('div');
  content.className = 'toast__content';
  const heading = document.createElement('strong');
  heading.textContent = title || (tone === 'danger' ? 'Não foi possível concluir' : 'Operação concluída');
  const text = document.createElement('span');
  text.textContent = message;
  content.append(heading, text);
  const close = document.createElement('button');
  close.className = 'toast__close';
  close.type = 'button';
  close.setAttribute('aria-label', 'Fechar notificação');
  close.textContent = '×';
  close.addEventListener('click', () => toast.remove());
  toast.append(content, close);
  elements.toastRegion.appendChild(toast);
  window.setTimeout(() => toast.remove(), 5000);
}

function readFilters() {
  const formData = new FormData(elements.filtersForm);
  return Object.fromEntries(
    Object.keys(defaultFilters).map((key) => [key, String(formData.get(key) || '').trim()]),
  );
}

function hydrateStateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  state.filters = Object.fromEntries(
    Object.keys(defaultFilters).map((key) => [key, String(params.get(key) || '').trim()]),
  );
  const page = Number(params.get('pagina'));
  const perPage = Number(params.get('porPagina'));
  const sortBy = params.get('ordenarPor');
  const order = params.get('ordem');
  state.table.page = Number.isInteger(page) && page > 0 ? page : 1;
  state.table.perPage = [10, 20, 50].includes(perPage) ? perPage : 10;
  state.table.sortBy = allowedSortFields.includes(sortBy) ? sortBy : 'data';
  state.table.order = ['asc', 'desc'].includes(order) ? order : 'desc';
}

function syncControlsFromState() {
  Object.entries(state.filters).forEach(([key, value]) => {
    const control = elements.filtersForm.elements.namedItem(key);
    if (control) control.value = value;
  });
  document.getElementById('pageSize').value = String(state.table.perPage);
  state.filters = readFilters();
}

function writeStateToUrl() {
  const params = new URLSearchParams();
  Object.entries(state.filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  if (state.table.page > 1) params.set('pagina', String(state.table.page));
  if (state.table.perPage !== 10) params.set('porPagina', String(state.table.perPage));
  if (state.table.sortBy !== 'data') params.set('ordenarPor', state.table.sortBy);
  if (state.table.order !== 'desc') params.set('ordem', state.table.order);
  const query = params.toString();
  const url = `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`;
  window.history.replaceState(null, '', url);
}

function renderActiveFilters() {
  elements.activeFilters.replaceChildren();
  const active = Object.entries(state.filters).filter(([, value]) => value);
  elements.activeFilters.hidden = active.length === 0;
  if (!active.length) return;
  const label = document.createElement('span');
  label.className = 'filter-chips__label';
  label.textContent = 'Filtros ativos:';
  elements.activeFilters.appendChild(label);
  active.forEach(([key, value]) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'filter-chip';
    button.dataset.filter = key;
    const displayValue = key.startsWith('data') ? formatDate(value) : value;
    button.textContent = `${filterLabels[key]}: ${displayValue}`;
    button.setAttribute('aria-label', `Remover filtro ${filterLabels[key]}: ${displayValue}`);
    elements.activeFilters.appendChild(button);
  });
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
  citySelect.onchange = syncUf;
  syncUf();
  const dates = state.cases.map((item) => item.data).filter(Boolean).sort();
  const predictionDate = document.getElementById('predictionDate');
  const predictionTime = document.getElementById('predictionTime');
  if (!predictionDate.value) predictionDate.value = dates.at(-1) || new Date().toISOString().slice(0, 10);
  if (!predictionTime.value) predictionTime.value = '18:30';
}

async function loadTable() {
  const requestId = ++tableRequestSequence;
  renderTableLoading();
  try {
    const payload = await api.paginatedCases({
      pagina: state.table.page,
      porPagina: state.table.perPage,
      ordenarPor: state.table.sortBy,
      ordem: state.table.order,
      ...state.filters,
    });
    if (requestId !== tableRequestSequence) return;
    state.table.page = payload.pagination.page || 1;
    renderOccurrencesTable(payload.items, payload.pagination);
    updateSortIndicators(payload.sorting.field, payload.sorting.order);
    writeStateToUrl();
  } catch (error) {
    if (requestId !== tableRequestSequence) return;
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
    const cards = document.getElementById('occurrenceCards');
    cards.replaceChildren();
    const mobileMessage = document.createElement('p');
    mobileMessage.className = 'empty-state';
    mobileMessage.textContent = message;
    cards.appendChild(mobileMessage);
    document.getElementById('tableSummary').textContent = 'Tabela temporariamente indisponível.';
    showToast(message, 'danger', 'Tabela indisponível');
  }
}

async function applyFilters({ resetPage = true, updateUrl = true } = {}) {
  state.filters = readFilters();
  if (resetPage) state.table.page = 1;
  applyLocalFilters();
  renderKpis();
  renderDataCharts();
  renderActiveFilters();
  if (updateUrl) writeStateToUrl();
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
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="5" class="empty-state">Métricas indisponíveis.</td></tr>';
    return;
  }
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
    renderFeaturesChart(null);
    renderMetricsChart([]);
    renderMetricsTable([]);
    document.getElementById('confusionMatrix').textContent = 'Matriz indisponível.';
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
    syncControlsFromState();
    applyLocalFilters();
    renderKpis();
    renderDataCharts();
    renderActiveFilters();
    await Promise.all([loadTable(), loadModelData()]);
    setApiStatus('success', status.modelo_disponivel ? 'API e modelo online' : 'API online');
    writeStateToUrl();
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
    const message = error instanceof ApiError ? error.message : 'Não foi possível executar a simulação.';
    result.textContent = message;
    showToast(message, 'danger', 'Falha na simulação');
  } finally {
    button.disabled = false;
    button.textContent = 'Executar simulação';
  }
}

function setupNavigationObserver() {
  const links = new Map(
    [...document.querySelectorAll('.topbar__nav a')]
      .map((link) => [link.getAttribute('href').slice(1), link]),
  );
  const sections = [...links.keys()].map((id) => document.getElementById(id)).filter(Boolean);
  if (!('IntersectionObserver' in window) || !sections.length) return;
  const observer = new IntersectionObserver((entries) => {
    const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    links.forEach((link, id) => {
      if (id === visible.target.id) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
  }, { rootMargin: '-20% 0px -65% 0px', threshold: [0.01, 0.2, 0.5] });
  sections.forEach((section) => observer.observe(section));
}

function bindEvents() {
  elements.filtersForm.addEventListener('submit', (event) => {
    event.preventDefault();
    applyFilters();
  });
  elements.filtersForm.addEventListener('change', (event) => {
    if (event.target.matches('select, input[type="date"]')) applyFilters();
  });
  document.getElementById('filterSearch').addEventListener('input', () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => applyFilters(), 400);
  });
  document.getElementById('clearFiltersButton').addEventListener('click', () => {
    elements.filtersForm.reset();
    applyFilters();
  });
  elements.activeFilters.addEventListener('click', (event) => {
    const button = event.target.closest('[data-filter]');
    if (!button) return;
    const control = elements.filtersForm.elements.namedItem(button.dataset.filter);
    if (control) control.value = '';
    applyFilters();
  });
  document.getElementById('exportButton').addEventListener('click', () => {
    try {
      downloadCsv(state.filteredCases);
      showToast(`${formatNumber(state.filteredCases.length)} registro(s) exportado(s) em CSV.`, 'success', 'Arquivo gerado');
    } catch (error) {
      showToast(error.message, 'danger', 'Exportação indisponível');
    }
  });
  document.getElementById('pageSize').addEventListener('change', (event) => {
    state.table.perPage = Number(event.target.value);
    state.table.page = 1;
    writeStateToUrl();
    loadTable();
  });
  document.getElementById('previousPage').addEventListener('click', () => {
    state.table.page = Math.max(1, state.table.page - 1);
    writeStateToUrl();
    loadTable();
  });
  document.getElementById('nextPage').addEventListener('click', () => {
    state.table.page += 1;
    writeStateToUrl();
    loadTable();
  });
  document.querySelectorAll('.sort-button').forEach((button) => {
    button.addEventListener('click', () => {
      const field = button.dataset.sort;
      if (state.table.sortBy === field) state.table.order = state.table.order === 'asc' ? 'desc' : 'asc';
      else { state.table.sortBy = field; state.table.order = 'asc'; }
      state.table.page = 1;
      writeStateToUrl();
      loadTable();
    });
  });
  document.querySelectorAll('.chart-data-toggle').forEach((button) => {
    button.addEventListener('click', () => {
      const target = document.getElementById(button.dataset.target);
      const expanded = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', String(!expanded));
      button.textContent = expanded ? 'Ver dados' : 'Ocultar dados';
      target.hidden = expanded;
    });
  });
  elements.predictionForm.addEventListener('submit', handlePrediction);
  document.getElementById('retryButton').addEventListener('click', loadDashboard);
  window.addEventListener('popstate', () => {
    hydrateStateFromUrl();
    syncControlsFromState();
    applyFilters({ resetPage: false, updateUrl: false });
  });
  setupNavigationObserver();
}

hydrateStateFromUrl();
bindEvents();
loadDashboard();
