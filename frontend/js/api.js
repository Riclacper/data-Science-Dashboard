import { API_URL, REQUEST_TIMEOUT_MS } from './config.js';

export class ApiError extends Error {
  constructor(message, status = 0, payload = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

async function requestOnce(path, options = {}) {
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


const RETRY_DELAYS_MS = [2500, 6000];

function wait(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

// Retry only safe GET requests and transient failures. Never repeat POST actions.
async function requestJson(path, options = {}) {
  const { onRetry, ...requestOptions } = options;
  const method = (requestOptions.method || 'GET').toUpperCase();
  const retries = method === 'GET' ? RETRY_DELAYS_MS.length : 0;

  for (let attempt = 0; ; attempt += 1) {
    try {
      return await requestOnce(path, requestOptions);
    } catch (error) {
      const transient = error instanceof ApiError && (
        error.status === 0 || error.status === 408 || error.status === 429 || error.status >= 500
      );
      if (!transient || attempt >= retries) throw error;
      if (typeof onRetry === 'function') onRetry(attempt + 2, retries + 1);
      await wait(RETRY_DELAYS_MS[attempt]);
    }
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
  status: (options = {}) => requestJson('/', options),
  health: () => requestJson('/health'),
  cases: (options = {}) => requestJson('/casos', options),
  paginatedCases: (params) => requestJson(`/casos/paginados${queryString(params)}`),
  features: () => requestJson('/features'),
  evaluation: () => requestJson('/avaliar-modelo'),
  classes: () => requestJson('/classes'),
  predict: (payload) => requestJson('/predict', { method: 'POST', body: JSON.stringify(payload) }),
};
