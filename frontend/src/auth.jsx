import { createContext, useContext, useEffect, useState } from "react";
import { api, setToken, getToken } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) { setLoading(false); return; }
    api.get("/auth/me")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  async function login(phone, password) {
    const data = await api.post("/auth/login", { phone, password });
    setToken(data.access);
    setUser(data.user);
    return data.user;
  }

  function logout() {
    setToken(null);
    setUser(null);
    window.location.hash = "#/login";
  }

  // Permission helper mirroring the backend RBAC codes.
  function can(code) {
    if (!user) return false;
    if (user.is_system_admin) return true;
    return (user.permission_codes || []).includes(code);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, can }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
