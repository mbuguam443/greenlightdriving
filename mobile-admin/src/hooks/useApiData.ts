import { useCallback, useEffect, useRef, useState } from 'react';

import { api, getErrorMessage } from '../services/apiClient';

export function useApiData<T>(path: string, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const mounted = useRef(true);

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      try {
        const { data: res } = await api.get<T>(path);
        if (mounted.current) {
          setData(res);
          setError('');
        }
      } catch (err) {
        if (mounted.current) setError(getErrorMessage(err));
      } finally {
        if (mounted.current) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [path]
  );

  useEffect(() => {
    mounted.current = true;
    load();
    return () => {
      mounted.current = false;
    };
  }, [load, ...deps]);

  const refresh = useCallback(() => load(true), [load]);

  return { data, loading, error, refreshing, refresh, setData };
}
