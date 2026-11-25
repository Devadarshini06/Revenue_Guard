import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  api,
  getStoredAccessToken,
  getStoredRefreshToken,
  setStoredTokens,
  clearStoredTokens,
} from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCurrentUser = useCallback(async () => {
    const token = getStoredAccessToken();
    if (!token) {
      setUser(null);
      setPermissions([]);
      setIsLoading(false);
      return;
    }

    try {
      const [meRes, permsRes] = await Promise.all([
        api.getMe(),
        api.getPermissions(),
      ]);

      setUser(meRes.user);
      setPermissions(permsRes.permissions || []);
    } catch (err) {
      console.warn('Authentication verification failed:', err.message);
      // If verification fails, clear stored tokens and reset user
      clearStoredTokens();
      setUser(null);
      setPermissions([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();

    // Listen for global auth expiration events from API interceptor
    const handleExpired = () => {
      setUser(null);
      setPermissions([]);
      clearStoredTokens();
    };

    window.addEventListener('rg:auth:expired', handleExpired);
    return () => window.removeEventListener('rg:auth:expired', handleExpired);
  }, [fetchCurrentUser]);

  const login = async (email, password) => {
    setIsLoading(true);
    try {
      const data = await api.login(email, password);
      setStoredTokens(data.access_token, data.refresh_token);
      setUser(data.user);

      // Fetch user's assigned RBAC permissions
      const permsRes = await api.getPermissions();
      setPermissions(permsRes.permissions || []);
      return data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    const refreshToken = getStoredRefreshToken();
    try {
      if (refreshToken) {
        await api.logout(refreshToken);
      }
    } catch (err) {
      console.warn('Server logout notice failed:', err.message);
    } finally {
      clearStoredTokens();
      setUser(null);
      setPermissions([]);
    }
  };

  const changePassword = async (currentPassword, newPassword) => {
    return api.changePassword(currentPassword, newPassword);
  };

  const hasPermission = (permission) => {
    if (!user) return false;
    if (user.role === 'Super Admin') return true;
    return permissions.includes(permission);
  };

  const value = {
    user,
    permissions,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    changePassword,
    hasPermission,
    refreshSession: fetchCurrentUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
