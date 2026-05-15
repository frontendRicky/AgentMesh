import { useCallback, useEffect, useRef, useState } from 'react';

export interface ApiEnvelope<T> {
  ok: boolean;
  data?: T;
  error?: { code: string; message: string; field?: string };
}

export interface ApiError {
  code: string;
  message: string;
  status?: number;
}

export async function apiGet<T>(url: string): Promise<T> {
  const res = await fetch(url);
  let body: ApiEnvelope<T>;
  try {
    body = (await res.json()) as ApiEnvelope<T>;
  } catch {
    throw { code: 'PARSE_ERROR', message: `非 JSON 响应 (${res.status})`, status: res.status } as ApiError;
  }
  if (!body.ok || body.data === undefined) {
    throw {
      code: body.error?.code ?? 'UNKNOWN',
      message: body.error?.message ?? `请求失败 (${res.status})`,
      status: res.status,
    } as ApiError;
  }
  return body.data;
}

export async function apiPost<T, B = unknown>(url: string, payload: B): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  let body: ApiEnvelope<T>;
  try {
    body = (await res.json()) as ApiEnvelope<T>;
  } catch {
    throw { code: 'PARSE_ERROR', message: `非 JSON 响应 (${res.status})`, status: res.status } as ApiError;
  }
  if (!body.ok || body.data === undefined) {
    throw {
      code: body.error?.code ?? 'UNKNOWN',
      message: body.error?.message ?? `请求失败 (${res.status})`,
      status: res.status,
    } as ApiError;
  }
  return body.data;
}

export interface UsePollingOptions {
  intervalMs?: number;
  enabled?: boolean;
}

export interface UsePollingResult<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  refresh: () => void;
}

export function usePolling<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
  options: UsePollingOptions = {},
): UsePollingResult<T> {
  const { intervalMs = 5000, enabled = true } = options;
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const tickRef = useRef(0);

  const tick = useCallback(async () => {
    const myTick = ++tickRef.current;
    try {
      const result = await fetcherRef.current();
      if (myTick !== tickRef.current) return;
      setData(result);
      setError(null);
    } catch (e) {
      if (myTick !== tickRef.current) return;
      setError(e as ApiError);
    } finally {
      if (myTick === tickRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }
    setLoading(true);
    void tick();
    const id = window.setInterval(() => {
      void tick();
    }, intervalMs);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, intervalMs, tick, ...deps]);

  return { data, error, loading, refresh: () => void tick() };
}
