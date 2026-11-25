import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  api,
  getAccessToken,
  setAccessToken,
  clearAccessToken,
} from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize session by checking for an active HttpOnly cookie via silent refresh
  const initializeSession = useCallback(async () => {
    try {
      const refreshData = await api.refresh();
      if (refreshData && refreshData.access_token) {
        setAccessToken(refreshData.access_token);
        const [meRes, permsRes] = await Promise.all([
          api.getMe(),
          api.getPermissions(),
        ]);
        setUser(meRes.user || meRes);
        setPermissions(permsRes.permissions || []);
      } else {
        clearAccessToken();
        setUser(null);
        setPermissions([]);
      }
    } catch {
      clearAccessToken();
      setUser(null);
      setPermissions([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    initializeSession();

    // Listen for global auth expiration events from API interceptor
    const handleExpired = () => {
      clearAccessToken();
      setUser(null);
      setPermissions([]);
    };

    window.addEventListener('rg:auth:expired', handleExpired);
    return () => window.removeEventListener('rg:auth:expired', handleExpired);
  }, [initializeSession]);

  const login = async (email, password) => {
    setIsLoading(true);
    try {
      const data = await api.login(email, password);
      setAccessToken(data.access_token);
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
    try {
      await api.logout();
    } catch (err) {
      console.warn('Server logout notice error:', err.message);
    } finally {
      clearAccessToken();
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
    refreshSession: initializeSession,
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
