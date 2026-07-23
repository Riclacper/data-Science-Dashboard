import { formatDate, formatNumber } from './utils.js';

function statusClass(status) {
  const normalized = String(status || '').toLowerCase();
  if (normalized.includes('investigação')) return 'status-pill--investigation';
  if (normalized.includes('concluído')) return 'status-pill--completed';
  if (normalized.includes('arquivado')) return 'status-pill--archived';
  return 'status-pill--analysis';
}

function createCell(value) {
  const cell = document.createElement('td');
  cell.textContent = value ?? '—';
  return cell;
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
      const pill = document.createElement('span');
      pill.className = `status-pill ${statusClass(item.status)}`;
      pill.textContent = item.status;
      statusCell.appendChild(pill);
      row.appendChild(statusCell);
      row.appendChild(createCell(formatDate(item.data)));
      row.appendChild(createCell(item.hora));
      row.appendChild(createCell(`${item.cidade}/${item.uf}`));
      row.appendChild(createCell(item.perito));
      body.appendChild(row);
    });
  }
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
}

export function updateSortIndicators(field, order) {
  document.querySelectorAll('.sort-button').forEach((button) => {
    button.removeAttribute('aria-sort');
    if (button.dataset.sort === field) {
      button.setAttribute('aria-sort', order === 'asc' ? 'ascending' : 'descending');
    }
  });
}
