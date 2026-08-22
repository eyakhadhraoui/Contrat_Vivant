import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('authToken') || null);
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('authUser');
    return saved ? JSON.parse(saved) : null;
  });

  const parseJwt = (token) => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (err) {
      return {};
    }
  };

  const login = async (username, password) => {
    const data = await authAPI.login(username, password);
    const payload = parseJwt(data.token);
    const userInfo = {
      username,
      role: payload.role || 'assurances',
      agence_id: payload.agence_id || null,
    };
    
    localStorage.setItem('authToken', data.token);
    localStorage.setItem('authUser', JSON.stringify(userInfo));
    setToken(data.token);
    setUser(userInfo);
    return data;
  };

  const signup = async (userData) => {
    const data = await authAPI.signup(userData);
    if (data.token) {
      const payload = parseJwt(data.token);
      const userInfo = {
        username: userData.username,
        role: userData.role || 'assurances',
        agence_id: userData.agence_id || null,
      };
      localStorage.setItem('authToken', data.token);
      localStorage.setItem('authUser', JSON.stringify(userInfo));
      setToken(data.token);
      setUser(userInfo);
    }
    return data;
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    setToken(null);
    setUser(null);
  };

  const isAssurances = user?.role?.toLowerCase().includes('assurances') ?? true;
  const isSinistres = user?.role?.toLowerCase().includes('sinistres') ?? false;

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        login,
        signup,
        logout,
        isAuthenticated: !!token,
        isAssurances,
        isSinistres,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
