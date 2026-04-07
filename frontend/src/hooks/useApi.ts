import { useState, useEffect, useCallback } from 'react';
import { ApiResponse } from '../services/api';

export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// Generic hook for API calls
export const useApi = <T>(
  apiCall: () => Promise<ApiResponse<T>>,
  dependencies: any[] = []
) => {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    // Skip API call if dependencies array contains false (e.g., isAuthenticated = false)
    if (dependencies.includes(false)) {
      console.log('[useApi] Skipping API call due to false dependency:', dependencies);
      setState({
        data: null,
        loading: false,
        error: null,
      });
      return Promise.resolve({ success: true, data: null });
    }

    console.log('[useApi] Starting API call with dependencies:', dependencies);
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await apiCall();
      console.log('[useApi] API response received:', response);

      if (response.success) {
        console.log('[useApi] API call successful, setting data:', response.data);
        setState({
          data: response.data || null,
          loading: false,
          error: null,
        });
      } else {
        const errorMsg = response.error?.message || 'An error occurred';
        console.error('[useApi] API call failed:', {
          error: response.error || 'Unknown error',
          errorMsg,
          dependencies
        });
        setState({
          data: null,
          loading: false,
          error: errorMsg,
        });
      }
    } catch (error) {
      console.error('[useApi] API call threw exception:', error);
      setState({
        data: null,
        loading: false,
        error: 'Network error occurred',
      });
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    ...state,
    refetch: fetchData,
  };
};

// Hook for mutation API calls (POST, PUT, DELETE)
export const useApiMutation = <TData, TVariables = void>() => {
  const [state, setState] = useState<{
    data: TData | null;
    loading: boolean;
    error: string | null;
  }>({
    data: null,
    loading: false,
    error: null,
  });

  const mutate = async (
    apiCall: (variables: TVariables) => Promise<ApiResponse<TData>>,
    variables: TVariables
  ) => {
    setState({ data: null, loading: true, error: null });

    try {
      const response = await apiCall(variables);

      if (response.success && response.data) {
        setState({
          data: response.data,
          loading: false,
          error: null,
        });
        return { success: true, data: response.data };
      } else {
        const errorMessage = response.error?.message || 'An error occurred';
        setState({
          data: null,
          loading: false,
          error: errorMessage,
        });
        return { success: false, error: errorMessage };
      }
    } catch (error) {
      const errorMessage = 'Network error occurred';
      setState({
        data: null,
        loading: false,
        error: errorMessage,
      });
      return { success: false, error: errorMessage };
    }
  };

  const reset = () => {
    setState({ data: null, loading: false, error: null });
  };

  return {
    ...state,
    mutate,
    reset,
  };
};
