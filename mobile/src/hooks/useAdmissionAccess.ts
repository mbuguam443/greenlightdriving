import { useCallback, useEffect, useRef, useState } from 'react';

import { api, getErrorMessage } from '../services/apiClient';
import { AdmissionAccess } from '../types';

export function useAdmissionAccess(enabled = true) {
  const [data, setData] = useState<AdmissionAccess | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const mounted = useRef(true);

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      try {
        const { data: res } = await api.get<AdmissionAccess>('/student/access/');
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
    []
  );

  useEffect(() => {
    mounted.current = true;
    if (enabled) load();
    else {
      setLoading(false);
      setData(null);
    }
    return () => {
      mounted.current = false;
    };
  }, [enabled, load]);

  const refresh = useCallback(() => load(true), [load]);

  return { data, loading, error, refreshing, refresh };
}
