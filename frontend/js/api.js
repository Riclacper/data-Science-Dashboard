import { API_URL, REQUEST_TIMEOUT_MS } from './config.js';

export class ApiError extends Error {
  constructor(message, status = 0, payload = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

async function requestJson(path, options = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(options.headers || {}),
      },
      signal: controller.signal,
    });

    const contentType = response.headers.get('content-type') || '';
    const payload = contentType.includes('application/json')
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      const message = payload?.erro || payload?.message || `Erro HTTP ${response.status}`;
      throw new ApiError(message, response.status, payload);
    }

    return payload;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new ApiError('A API demorou mais que o esperado para responder.');
    }
    if (error instanceof ApiError) throw error;
    throw new ApiError('Não foi possível conectar à API.');
  } finally {
    window.clearTimeout(timeout);
  }
}

function queryString(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) query.set(key, String(value));
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : '';
}

export const api = {
  status: () => requestJson('/'),
  health: () => requestJson('/health'),
  cases: () => requestJson('/casos'),
  paginatedCases: (params) => requestJson(`/casos/paginados${queryString(params)}`),
  features: () => requestJson('/features'),
  evaluation: () => requestJson('/avaliar-modelo'),
  classes: () => requestJson('/classes'),
  predict: (payload) => requestJson('/predict', { method: 'POST', body: JSON.stringify(payload) }),
};
