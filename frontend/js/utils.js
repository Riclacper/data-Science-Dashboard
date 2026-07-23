export function formatNumber(value) {
  return new Intl.NumberFormat('pt-BR').format(Number(value) || 0);
}

export function formatDate(value) {
  if (!value) return '—';
  const [year, month, day] = String(value).split('-').map(Number);
  if (!year || !month || !day) return String(value);
  return new Intl.DateTimeFormat('pt-BR').format(new Date(year, month - 1, day));
}

export function formatPercent(value, fractionDigits = 0) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '—';
  return `${(numeric * 100).toFixed(fractionDigits)}%`;
}

export function countBy(items, field) {
  return items.reduce((accumulator, item) => {
    const key = item[field] || 'Não informado';
    accumulator[key] = (accumulator[key] || 0) + 1;
    return accumulator;
  }, {});
}

export function topEntry(counts) {
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0] || ['—', 0];
}

export function uniqueSorted(items, field) {
  return [...new Set(items.map((item) => item[field]).filter(Boolean))]
    .sort((a, b) => String(a).localeCompare(String(b), 'pt-BR'));
}

export function fillSelect(select, values, placeholder = null) {
  const currentValue = select.value;
  select.replaceChildren();
  if (placeholder !== null) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = placeholder;
    select.appendChild(option);
  }
  values.forEach((value) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
  if ([...select.options].some((option) => option.value === currentValue)) select.value = currentValue;
}

function csvCell(value) {
  const normalized = value === null || value === undefined
    ? ''
    : typeof value === 'object' ? JSON.stringify(value) : String(value);
  return `"${normalized.replaceAll('"', '""')}"`;
}

export function downloadCsv(items, filename = 'ocorrencias_filtradas.csv') {
  if (!items.length) throw new Error('Nenhum registro disponível para exportação.');
  const columns = [
    ['id', 'ID'], ['tipoCrime', 'Tipo'], ['status', 'Status'], ['data', 'Data'],
    ['hora', 'Hora'], ['cidade', 'Cidade'], ['uf', 'UF'], ['descricao', 'Descrição'], ['perito', 'Equipe'],
  ];
  const rows = [
    columns.map(([, label]) => csvCell(label)).join(','),
    ...items.map((item) => columns.map(([key]) => csvCell(item[key])).join(',')),
  ];
  const blob = new Blob([`\uFEFF${rows.join('\n')}`], { type: 'text/csv;charset=utf-8' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function featureLabel(feature) {
  const labels = {
    tipoCrime: 'Tipo da ocorrência', cidade: 'Cidade', uf: 'Estado (UF)',
    hora_num: 'Hora da ocorrência', dias_desde_ocorrencia: 'Tempo desde a ocorrência',
  };
  return labels[feature] || feature;
}
