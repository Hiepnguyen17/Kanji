import { useEffect, useState } from 'react';

// VITE_API_BASE_URL is empty in Docker because Nginx proxies the API through
// the same public domain. Development keeps the local FastAPI default.
const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL;
export const API_BASE_URL = (configuredApiBaseUrl === undefined ? 'http://localhost:8010' : configuredApiBaseUrl).replace(/\/$/, '');
export const API_ORIGIN = API_BASE_URL ? new URL(API_BASE_URL).origin : window.location.origin;

export const apiUrl = path => {
  if (!path) return API_BASE_URL;
  if (/^https?:\/\//.test(path)) {
    return path.startsWith('http://localhost:8010')
      ? `${API_BASE_URL}${path.slice('http://localhost:8010'.length)}`
      : path;
  }
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
};

export const apiFetch = (path, options) => fetch(apiUrl(path), {
  credentials: 'include',
  ...options,
});

export function useRemoteJson(path) {
  const [result, setResult] = useState({ path, status: 'loading', data: null });
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    if (!path) {
      setResult({ path, status: 'loading', data: null });
      return undefined;
    }
    const controller = new AbortController();
    setResult({ path, status: 'loading', data: null });
    apiFetch(path, { signal: controller.signal })
      .then(async response => {
        if (controller.signal.aborted) return;
        if (response.status === 404) {
          setResult({ path, status: 'notfound', data: null });
          return;
        }
        if (!response.ok) throw new Error('API unavailable');
        const data = await response.json();
        if (!controller.signal.aborted) {
          setResult({ path, status: Array.isArray(data) && data.length === 0 ? 'empty' : 'ready', data });
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setResult({ path, status: 'error', data: null });
      });
    return () => controller.abort();
  }, [path, retry]);

  return {
    status: result.path === path ? result.status : 'loading',
    data: result.path === path ? result.data : null,
    retry: () => setRetry(value => value + 1),
  };
}
