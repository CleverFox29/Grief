import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('cgas_token'));
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('cgas_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);
  const [sessionWarning, setSessionWarning] = useState(null);

  const inactivityTimerRef = useRef(null);
  const INACTIVITY_TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes as per NFR 4.2

  // Inactivity timeout handler
  const resetInactivityTimer = () => {
    if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
    if (token) {
      inactivityTimerRef.current = setTimeout(() => {
        logout("Your session expired due to 15 minutes of inactivity.");
      }, INACTIVITY_TIMEOUT_MS);
    }
  };

  useEffect(() => {
    const activityEvents = ['mousedown', 'keydown', 'touchstart', 'scroll'];
    const handleActivity = () => resetInactivityTimer();

    activityEvents.forEach(e => window.addEventListener(e, handleActivity));
    resetInactivityTimer();

    return () => {
      activityEvents.forEach(e => window.removeEventListener(e, handleActivity));
      if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
    };
  }, [token]);

  // Global 401 Unauthorized interceptor to gracefully handle expired/invalid sessions
  useEffect(() => {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const response = await originalFetch(...args);
      if (response.status === 401) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0]?.url || '');
        if (!url.includes('/api/auth/login')) {
          logout("Your session has expired or token is invalid. Please log in again.");
        }
      }
      return response;
    };
    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  const login = async (role, userId, password) => {
    setLoading(true);
    setSessionWarning(null);
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role,
          user_id: userId,
          password
        }),
      });

      const responseText = await response.text();
      let data = {};
      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch (jsonErr) {
        if (!response.ok) {
          const preview = responseText.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 160);
          throw new Error(
            `Backend Error (HTTP ${response.status}${response.statusText ? ' ' + response.statusText : ''}): ` +
            (preview || 'Server returned a non-JSON response. Check Vercel function logs.')
          );
        }
      }

      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('cgas_token', data.access_token);
      localStorage.setItem('cgas_user', JSON.stringify(data.user));
      resetInactivityTimer();
      return { success: true, user: data.user };
    } catch (err) {
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const logout = (reason = null) => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('cgas_token');
    localStorage.removeItem('cgas_user');
    if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
    if (reason) setSessionWarning(reason);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        loading,
        sessionWarning,
        setSessionWarning,
        login,
        logout,
        isAuthenticated: !!token && !!user
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
}
