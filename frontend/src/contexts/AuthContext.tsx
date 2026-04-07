import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/router';
import { getAuthToken, removeAuthToken } from '../services/api';
import { authService, User } from '../services/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (userData: User, token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // 只在首次挂载时初始化认证
    if (initialized) return;
    
    const initAuth = async () => {
      const token = getAuthToken();
      console.log('[AuthProvider] Initializing auth, token:', token ? 'exists' : 'missing');

      if (!token) {
        console.log('[AuthProvider] No token found, setting not authenticated');
        setLoading(false);
        setIsAuthenticated(false);
        return;
      }

      // 如果有 token，验证它
      console.log('[AuthProvider] Token found, verifying with profile request...');

      try {
        const response = await authService.getProfile();
        console.log('[AuthProvider] Profile response:', response);

        if (response.success && response.data) {
          console.log('[AuthProvider] Token validation successful, user:', response.data);
          setUser(response.data);
          setIsAuthenticated(true);
        } else {
          console.log('[AuthProvider] Token validation failed, removing invalid token');
          removeAuthToken();
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (error) {
        console.error('[AuthProvider] Token validation failed:', error);
        removeAuthToken();
        setIsAuthenticated(false);
        setUser(null);
      } finally {
        setLoading(false);
        setInitialized(true);
        console.log('[AuthProvider] Auth initialization complete');
      }
    };

    initAuth();
  }, [initialized]);

  const login = (userData: User, token: string) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    removeAuthToken();
    router.push('/login');
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated,
    login,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// 便捷的 hooks
export const useAuthGuard = (redirectTo: string = '/login') => {
  const { user, isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, loading, router, redirectTo]);

  return { user, isAuthenticated, loading };
};

export const useOptionalAuth = () => {
  const { user, isAuthenticated, loading, login, logout } = useAuth();
  
  return {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    isAnonymous: !isAuthenticated && !loading
  };
};