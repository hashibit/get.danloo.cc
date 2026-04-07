// API configuration and utility functions
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

// Get auth token from localStorage
export const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
};

// Set auth token in localStorage
export const setAuthToken = (token: string): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('auth_token', token);
  }
};

// Remove auth token from localStorage
export const removeAuthToken = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('auth_token');
  }
};

// Create headers with auth token
const createHeaders = (includeAuth: boolean = true): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (includeAuth) {
    const token = getAuthToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  return headers;
};

// Create headers for multipart form data
const createFormHeaders = (includeAuth: boolean = true): HeadersInit => {
  const headers: HeadersInit = {};

  if (includeAuth) {
    const token = getAuthToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  return headers;
};

// Generic API request function
export const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {},
  includeAuth: boolean = true
): Promise<ApiResponse<T>> => {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = options.body instanceof FormData
      ? createFormHeaders(includeAuth)
      : createHeaders(includeAuth);

    console.log('[apiRequest] Making request to:', url);
    console.log('[apiRequest] Request headers:', headers);
    console.log('[apiRequest] Request options:', options);
    console.log('[apiRequest] Request method:', options.method || 'GET');
    console.log('[apiRequest] Request body:', options.body);

    const response = await fetch(url, {
      headers,
      mode: 'cors',
      ...options,
    });

    console.log('[apiRequest] Response status:', response.status);
    console.log('[apiRequest] Response headers:', Object.fromEntries(response.headers.entries()));

    const contentType = response.headers.get('content-type');
    let data;

    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    console.log('[apiRequest] Response data:', data);

    if (!response.ok) {
      const errorResult = {
        success: false,
        error: {
          code: response.status.toString(),
          message: data?.error?.message || data?.detail || 'An error occurred',
          details: data?.error?.details || data
        }
      };
      console.error('[apiRequest] Request failed:', errorResult);
      return errorResult;
    }

    const successResult = {
      success: true,
      data
    };
    console.log('[apiRequest] Request successful:', successResult);
    return successResult;
  } catch (error) {
    console.error('[apiRequest] Request threw exception:', error);
    return {
      success: false,
      error: {
        code: 'NETWORK_ERROR',
        message: 'Network error occurred',
        details: error
      }
    };
  }
};

export default API_BASE_URL;
