import { formatDate, formatNumber } from './utils.js';

function statusClass(status) {
  const normalized = String(status || '').toLowerCase();
  if (normalized.includes('investigação')) return 'status-pill--investigation';
  if (normalized.includes('concluído')) return 'status-pill--completed';
  if (normalized.includes('arquivado')) return 'status-pill--archived';
  return 'status-pill--analysis';
}

function createStatusPill(status) {
  const pill = document.createElement('span');
  pill.className = `status-pill ${statusClass(status)}`;
  pill.textContent = status || 'Não informado';
  return pill;
}

function createCell(value) {
  const cell = document.createElement('td');
  cell.textContent = value ?? '—';
  return cell;
}

function createDetail(term, value) {
  const wrapper = document.createElement('div');
  const dt = document.createElement('dt');
  const dd = document.createElement('dd');
  dt.textContent = term;
  dd.textContent = value || '—';
  wrapper.append(dt, dd);
  return wrapper;
}

function renderOccurrenceCards(items) {
  const container = document.getElementById('occurrenceCards');
  container.replaceChildren();
  if (!items.length) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = 'Nenhuma ocorrência encontrada com os filtros atuais.';
    container.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'occurrence-card';
    const header = document.createElement('div');
    header.className = 'occurrence-card__header';
    const title = document.createElement('div');
    const id = document.createElement('span');
    id.className = 'occurrence-card__id';
    id.textContent = `#${item.id}`;
    const type = document.createElement('strong');
    type.textContent = item.tipoCrime || 'Tipo não informado';
    title.append(id, type);
    header.append(title, createStatusPill(item.status));
    const details = document.createElement('dl');
    details.append(
      createDetail('Data e hora', `${formatDate(item.data)} às ${item.hora || '—'}`),
      createDetail('Local', `${item.cidade || '—'}/${item.uf || '—'}`),
      createDetail('Equipe', item.perito),
      createDetail('Descrição', item.descricao),
    );
    card.append(header, details);
    container.appendChild(card);
  });
}

export function renderOccurrencesTable(items, pagination) {
  const body = document.getElementById('occurrencesTableBody');
  body.replaceChildren();
  if (!items.length) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 7;
    cell.className = 'empty-state';
    cell.textContent = 'Nenhuma ocorrência encontrada com os filtros atuais.';
    row.appendChild(cell);
    body.appendChild(row);
  } else {
    items.forEach((item) => {
      const row = document.createElement('tr');
      row.appendChild(createCell(`#${item.id}`));
      row.appendChild(createCell(item.tipoCrime));
      const statusCell = document.createElement('td');
      statusCell.appendChild(createStatusPill(item.status));
      row.appendChild(statusCell);
      row.appendChild(createCell(formatDate(item.data)));
      row.appendChild(createCell(item.hora));
      row.appendChild(createCell(`${item.cidade}/${item.uf}`));
      row.appendChild(createCell(item.perito));
      body.appendChild(row);
    });
  }
  renderOccurrenceCards(items);
  document.getElementById('tableSummary').textContent = pagination.total
    ? `${formatNumber(pagination.total)} registro(s) encontrado(s).`
    : 'Nenhum registro encontrado.';
  document.getElementById('paginationInfo').textContent = pagination.pages
    ? `Página ${pagination.page} de ${pagination.pages}`
    : 'Página 0 de 0';
  document.getElementById('previousPage').disabled = !pagination.hasPrevious;
  document.getElementById('nextPage').disabled = !pagination.hasNext;
}

export function renderTableLoading() {
  const body = document.getElementById('occurrencesTableBody');
  body.innerHTML = '<tr><td colspan="7" class="empty-state">Carregando registros...</td></tr>';
  const cards = document.getElementById('occurrenceCards');
  cards.innerHTML = '<div class="occurrence-card"><strong>Carregando registros...</strong><div class="skeleton-block" style="height: 70px">.</div></div>';
}

export function updateSortIndicators(field, order) {
  document.querySelectorAll('.sort-button').forEach((button) => {
    button.removeAttribute('aria-sort');
    if (button.dataset.sort === field) {
      button.setAttribute('aria-sort', order === 'asc' ? 'ascending' : 'descending');
    }
  });
}
