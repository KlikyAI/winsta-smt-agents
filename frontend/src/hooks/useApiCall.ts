import { useState, useCallback } from 'react';
import { useToast } from '../context/ToastContext';

export interface UseApiCallOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  successTitle?: string;
  successMessage?: string;
  errorTitle?: string;
  showToastOnError?: boolean;
}

export function useApiCall<T, Args extends any[] = any[]>(
  apiFn: (...args: Args) => Promise<T>,
  options: UseApiCallOptions<T> = {}
) {
  const { addToast } = useToast();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(
    async (...args: Args): Promise<T | null> => {
      setLoading(true);
      setError(null);

      try {
        const result = await apiFn(...args);
        setData(result);

        if (options.successTitle) {
          addToast('success', options.successTitle, options.successMessage);
        }

        if (options.onSuccess) {
          options.onSuccess(result);
        }

        return result;
      } catch (err: any) {
        const errMsg = err?.message || 'Terjadi kesalahan sistem';
        setError(errMsg);

        if (options.showToastOnError !== false) {
          addToast('error', options.errorTitle || 'Permintaan Gagal', errMsg);
        }

        if (options.onError) {
          options.onError(err instanceof Error ? err : new Error(errMsg));
        }

        return null;
      } finally {
        setLoading(false);
      }
    },
    [apiFn, options, addToast]
  );

  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
    setData,
  };
}

